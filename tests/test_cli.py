import csv
import json
from pathlib import Path
import subprocess
import sys

import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
CLI = (
    ROOT
    / "plugins"
    / "fuse-bead-designer"
    / "skills"
    / "create-fuse-bead-patterns"
    / "scripts"
    / "create_pattern.py"
)


@pytest.fixture
def clean_subject_path(tmp_path):
    path = tmp_path / "subject.png"
    image = Image.new("RGBA", (58, 29), (0, 0, 0, 0))
    for column in range(8, 50):
        for row in range(5, 24):
            image.putpixel((column, row), (229, 57, 53, 255))
    image.save(path)
    return path


def run_cli(subject, output_dir, *options, cwd=None):
    return subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(subject),
            "--output-dir",
            str(output_dir),
            *options,
        ],
        text=True,
        capture_output=True,
        cwd=cwd,
    )


def read_pattern(output_dir):
    return json.loads((output_dir / "pattern.json").read_text(encoding="utf-8"))


def test_cli_creates_all_verified_outputs_from_any_working_directory(tmp_path, clean_subject_path):
    output = tmp_path / "out"

    result = run_cli(
        clean_subject_path,
        output,
        "--width",
        "29",
        "--height",
        "29",
        "--verification",
        "verified",
        "--classification",
        "pixel-art",
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert {path.name for path in output.iterdir()} == {
        "template.png",
        "pattern.json",
        "colors.csv",
        "report.json",
    }


def test_cli_automatically_selects_a_standard_board(tmp_path, clean_subject_path):
    output = tmp_path / "out"

    result = run_cli(clean_subject_path, output)

    assert result.returncode == 0, result.stderr
    pattern = read_pattern(output)
    assert pattern["board_layout"] == {
        "columns": 2,
        "rows": 1,
        "is_custom_size": False,
    }
    assert (pattern["width"], pattern["height"]) == (58, 29)


@pytest.mark.parametrize("option", ["--width", "--height"])
def test_cli_requires_width_and_height_together(tmp_path, clean_subject_path, option):
    result = run_cli(clean_subject_path, tmp_path / "out", option, "29")

    assert result.returncode == 2
    assert "--width and --height must be provided together" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("colors", ["7", "17", "not-a-number"])
def test_cli_rejects_invalid_color_limits(tmp_path, clean_subject_path, colors):
    result = run_cli(clean_subject_path, tmp_path / "out", "--colors", colors)

    assert result.returncode == 2
    assert "--colors must be an integer from 8 through 16" in result.stderr


def test_cli_refuses_unconfirmed_large_board(tmp_path, clean_subject_path):
    result = run_cli(
        clean_subject_path,
        tmp_path / "out",
        "--width",
        "87",
        "--height",
        "87",
    )

    assert result.returncode == 2
    assert "more than four boards" in result.stderr


def test_cli_allows_confirmed_large_board(tmp_path, clean_subject_path):
    output = tmp_path / "out"
    result = run_cli(
        clean_subject_path,
        output,
        "--width",
        "87",
        "--height",
        "87",
        "--confirm-large-board",
    )

    assert result.returncode == 0, result.stderr
    assert read_pattern(output)["board_layout"]["columns"] == 3
    assert read_pattern(output)["board_layout"]["rows"] == 3


@pytest.mark.parametrize(
    ("option", "value", "message"),
    [
        ("--inferred-cells", "not-a-coordinate", "coordinates must use column,row"),
        ("--protect-cells", "29,0", "coordinate is outside the selected grid"),
    ],
)
def test_cli_rejects_invalid_coordinate_options(tmp_path, clean_subject_path, option, value, message):
    result = run_cli(
        clean_subject_path,
        tmp_path / "out",
        "--width",
        "29",
        "--height",
        "29",
        option,
        value,
    )

    assert result.returncode == 2
    assert message in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_loads_the_requested_palette_without_fabricating_brand_metadata(tmp_path, clean_subject_path):
    palette = tmp_path / "palette.json"
    palette.write_text(
        json.dumps(
            [
                {
                    "id": "only-red",
                    "name": "Only Red",
                    "name_zh": "仅红",
                    "hex": "#E53935",
                }
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "out"

    result = run_cli(
        clean_subject_path,
        output,
        "--width",
        "29",
        "--height",
        "29",
        "--palette",
        str(palette),
    )

    assert result.returncode == 0, result.stderr
    assert read_pattern(output)["palette"] == [
        {
            "id": "only-red",
            "name": "Only Red",
            "name_zh": "仅红",
            "hex": "#E53935",
            "brand_code": None,
        }
    ]
    with (output / "colors.csv").open(encoding="utf-8", newline="") as stream:
        assert list(csv.DictReader(stream))[0]["brand_code"] == ""


def test_cli_creates_review_output_for_inferred_cells(tmp_path, clean_subject_path):
    output = tmp_path / "out"
    result = run_cli(
        clean_subject_path,
        output,
        "--width",
        "29",
        "--height",
        "29",
        "--verification",
        "inferred-low",
        "--inferred-cells",
        "0,0",
    )

    assert result.returncode == 0, result.stderr
    assert (output / "review.png").is_file()
    assert read_pattern(output)["inferred_cells"] == [[0, 0]]


def test_cli_guards_nonempty_output_and_force_preserves_unrelated_files(tmp_path, clean_subject_path):
    output = tmp_path / "out"
    output.mkdir()
    note = output / "keep.txt"
    note.write_text("preserve me", encoding="utf-8")

    refused = run_cli(clean_subject_path, output)

    assert refused.returncode == 2
    assert "non-empty output directory" in refused.stderr
    assert not (output / "pattern.json").exists()

    forced = run_cli(clean_subject_path, output, "--force")

    assert forced.returncode == 0, forced.stderr
    assert note.read_text(encoding="utf-8") == "preserve me"


def test_cli_outputs_have_count_agreement_and_report_options(tmp_path, clean_subject_path):
    output = tmp_path / "out"
    result = run_cli(
        clean_subject_path,
        output,
        "--width",
        "29",
        "--height",
        "29",
        "--classification",
        "pixel-art",
        "--removed-interference",
        "table",
        "watermark",
    )

    assert result.returncode == 0, result.stderr
    pattern = read_pattern(output)
    with (output / "colors.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert pattern["total_beads"] == sum(int(row["count"]) for row in rows)
    assert report["classification"] == "pixel-art"
    assert report["removed_interference"] == ["table", "watermark"]
