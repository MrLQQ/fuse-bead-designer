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
    image = Image.new("RGBA", (232, 116), (0, 0, 0, 0))
    for column in range(32, 200):
        for row in range(20, 96):
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


def test_cli_rejects_high_resolution_image_without_a_pattern_draft(
    tmp_path, clean_subject_path
):
    result = run_cli(
        clean_subject_path,
        tmp_path / "out",
        "--classification",
        "high-resolution-image",
    )

    assert result.returncode == 2
    assert "high-resolution-image requires has_pattern_draft=True" in result.stderr


def test_cli_accepts_high_resolution_image_with_a_pattern_draft(tmp_path, clean_subject_path):
    result = run_cli(
        clean_subject_path,
        tmp_path / "out",
        "--classification",
        "high-resolution-image",
        "--draft-input",
        str(clean_subject_path),
        "--width",
        "29",
        "--height",
        "29",
    )

    assert result.returncode == 0, result.stderr


def test_cli_compiles_high_resolution_draft_and_records_original_provenance(tmp_path):
    source = tmp_path / "source.png"
    draft = tmp_path / "draft.png"
    Image.new("RGBA", (4, 4), (229, 57, 53, 255)).save(source)
    Image.new("RGBA", (4, 4), (17, 21, 21, 255)).save(draft)
    output = tmp_path / "out"

    result = run_cli(
        source,
        output,
        "--classification",
        "high-resolution-image",
        "--draft-input",
        str(draft),
        "--width",
        "1",
        "--height",
        "1",
    )

    assert result.returncode == 0, result.stderr
    pattern = read_pattern(output)
    assert pattern["cells"] == [["black"]]
    assert pattern["settings"]["draft_used"] is True
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["source_input"] == str(source)
    assert report["draft_input"] == str(draft)
    assert report["compiled_input"] == str(draft)


def test_cli_requests_dimensions_for_ambiguous_pattern_draft(
    tmp_path, clean_subject_path
):
    result = run_cli(
        clean_subject_path,
        tmp_path / "out",
        "--classification",
        "pattern-draft",
    )

    assert result.returncode == 2
    assert "provide --width and --height" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_rejects_nonpositive_grid_box(tmp_path, clean_subject_path):
    result = run_cli(
        clean_subject_path,
        tmp_path / "out",
        "--grid-box",
        "0,0,0,29",
    )

    assert result.returncode == 2
    assert "grid box must have positive width and height" in result.stderr


def test_cli_rejects_grid_box_outside_the_input_image(tmp_path, clean_subject_path):
    result = run_cli(
        clean_subject_path,
        tmp_path / "out",
        "--grid-box",
        "0,0,233,116",
    )

    assert result.returncode == 2
    assert "grid box must be within image bounds" in result.stderr


def test_cli_records_explicit_sampling_override(tmp_path, clean_subject_path):
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
        "--sampling",
        "median",
    )

    assert result.returncode == 0, result.stderr
    assert read_pattern(output)["settings"]["sampling"] == "median"


def test_cli_records_explicit_cleanup_override(tmp_path, clean_subject_path):
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
        "--cleanup",
    )

    assert result.returncode == 0, result.stderr
    assert read_pattern(output)["settings"]["cleanup"] is True


def test_cli_preserves_explicit_exact_grid_dimensions_and_occupied_cells(tmp_path):
    source = tmp_path / "exact-grid.png"
    image = Image.new("RGBA", (68 * 4, 60 * 4), (0, 0, 0, 0))
    for column, row in ((0, 0), (34, 29), (67, 59)):
        image.putpixel((column * 4 + 1, row * 4 + 1), (229, 57, 53, 255))
    image.save(source)
    output = tmp_path / "out"

    result = run_cli(
        source,
        output,
        "--classification",
        "pixel-art",
        "--width",
        "68",
        "--height",
        "60",
        "--confirm-large-board",
    )

    assert result.returncode == 0, result.stderr
    pattern = read_pattern(output)
    assert (pattern["width"], pattern["height"]) == (68, 60)
    assert pattern["board_layout"] == {
        "columns": 3,
        "rows": 3,
        "is_custom_size": True,
    }
    assert pattern["total_beads"] == 3
    assert pattern["settings"] == {
        "colors": 16,
        "max_boards": 4,
        "source_classification": "pixel-art",
        "sampling": "center",
        "cleanup": False,
        "grid_box": None,
        "draft_used": False,
        "grid_evidence": {
            "source": "declared",
            "confidence": 1.0,
            "width": 68,
            "height": 60,
            "box": [0, 0, 272, 240],
        },
        "source_input": str(source),
        "draft_input": None,
        "compiled_input": str(source),
        "protected_cells": [],
    }
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["classification"] == "pixel-art"
    assert report["source_classification"] == "pixel-art"
    assert report["sampling"] == "center"
    assert report["cleanup"] is False
    assert report["grid_box"] is None
    assert report["draft_used"] is False
    assert report["grid_evidence"] == pattern["settings"]["grid_evidence"]


def test_cli_recovers_unambiguous_exact_grid_dimensions(tmp_path):
    logical = Image.new("RGBA", (16, 16))
    logical.putdata(
        [
            (17, 21, 21, 255) if (column + row) % 2 == 0 else (229, 57, 53, 255)
            for row in range(16)
            for column in range(16)
        ]
    )
    source = tmp_path / "scaled-grid.png"
    logical.resize((80, 80), Image.Resampling.NEAREST).save(source)
    output = tmp_path / "out"

    result = run_cli(source, output, "--classification", "pixel-art")

    assert result.returncode == 0, result.stderr
    pattern = read_pattern(output)
    assert (pattern["width"], pattern["height"]) == (16, 16)
    assert pattern["total_beads"] == 16 * 16
    assert pattern["settings"]["grid_box"] == [0, 0, 80, 80]
    assert pattern["settings"]["grid_evidence"] == {
        "source": "nearest-neighbor",
        "confidence": 1.0,
        "width": 16,
        "height": 16,
        "box": [0, 0, 80, 80],
    }


def test_cli_legacy_resample_selects_compatibility_policy(tmp_path, clean_subject_path):
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
        "--legacy-resample",
    )

    assert result.returncode == 0, result.stderr
    settings = read_pattern(output)["settings"]
    assert settings["sampling"] == "median"
    assert settings["cleanup"] is True


def test_cli_legacy_resample_uses_original_instead_of_high_resolution_draft(tmp_path):
    source = tmp_path / "source.png"
    draft = tmp_path / "draft.png"
    Image.new("RGBA", (4, 4), (229, 57, 53, 255)).save(source)
    Image.new("RGBA", (4, 4), (17, 21, 21, 255)).save(draft)
    output = tmp_path / "out"

    result = run_cli(
        source,
        output,
        "--classification",
        "high-resolution-image",
        "--draft-input",
        str(draft),
        "--width",
        "1",
        "--height",
        "1",
        "--legacy-resample",
    )

    assert result.returncode == 0, result.stderr
    pattern = read_pattern(output)
    assert pattern["cells"] == [["red"]]
    assert pattern["settings"]["draft_used"] is False
    assert pattern["settings"]["sampling"] == "median"
    assert pattern["settings"]["cleanup"] is True


def test_cli_rejects_unrectified_finished_bead_photo(tmp_path, clean_subject_path):
    result = run_cli(
        clean_subject_path,
        tmp_path / "out",
        "--classification",
        "finished-bead-photo",
    )

    assert result.returncode == 2
    assert "finished-bead-photo requires rectified_grid=True" in result.stderr


def test_cli_accepts_rectified_finished_bead_photo(tmp_path, clean_subject_path):
    result = run_cli(
        clean_subject_path,
        tmp_path / "out",
        "--classification",
        "finished-bead-photo",
        "--rectified-grid",
        "--width",
        "29",
        "--height",
        "29",
    )

    assert result.returncode == 0, result.stderr


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
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["inferred_cells"] == [[0, 0]]


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


def test_cli_force_failure_does_not_partially_publish_generated_artifacts(
    tmp_path, clean_subject_path
):
    output = tmp_path / "out"
    output.mkdir()
    template = output / "template.png"
    template.mkdir()
    marker = template / "keep.txt"
    marker.write_text("existing template directory", encoding="utf-8")
    prior_report = output / "report.json"
    prior_report.write_text("old report", encoding="utf-8")
    unrelated = output / "unrelated.txt"
    unrelated.write_text("preserve me", encoding="utf-8")

    result = run_cli(clean_subject_path, output, "--force")

    assert result.returncode == 2
    assert "generated artifact target is not a regular file: template.png" in result.stderr
    assert marker.read_text(encoding="utf-8") == "existing template directory"
    assert prior_report.read_text(encoding="utf-8") == "old report"
    assert unrelated.read_text(encoding="utf-8") == "preserve me"
    assert not (output / "pattern.json").exists()
    assert not (output / "colors.csv").exists()
    assert not (output / "review.png").exists()


def test_cli_loads_csv_palette_and_preserves_brand_code(tmp_path, clean_subject_path):
    palette = tmp_path / "palette.csv"
    palette.write_text(
        "id,name,name_zh,hex,brand_code\nred,Red,红色,#E53935,R-01\n",
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
    assert read_pattern(output)["palette"][0]["brand_code"] == "R-01"
    with (output / "colors.csv").open(encoding="utf-8", newline="") as stream:
        assert list(csv.DictReader(stream))[0]["brand_code"] == "R-01"


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
