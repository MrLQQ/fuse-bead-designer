import json
from pathlib import Path
import subprocess
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = (
    ROOT
    / "plugins"
    / "fuse-bead-designer"
    / "skills"
    / "create-fuse-bead-patterns"
)
CLI = SKILL_ROOT / "scripts/create_pattern.py"
FIXTURE = ROOT / "tests/fixtures/complex-logical-pattern.png"

CELL_SCALE = 4
DISPLAY_PADDING = 8
GRID_BOX = (8, 8, 156, 172)
GRID_SIZE = (37, 41)
COLORS = {
    "outline": "#11181D",
    "shadow": "#17242B",
    "body": "#24323A",
    "turquoise": "#1FB8AE",
    "eye": "#F7F3E8",
    "yellow": "#F4C542",
    "orange": "#E86A33",
    "purple": "#7C4D9A",
}
FEATURES = {
    (13, 17): "eye",
    (23, 17): "eye",
    (17, 10): "orange",
    (18, 9): "yellow",
    (19, 10): "purple",
    (8, 13): "turquoise",
    (7, 14): "turquoise",
    (6, 15): "turquoise",
    (28, 13): "turquoise",
    (29, 14): "turquoise",
    (30, 15): "turquoise",
    (10, 27): "yellow",
    (26, 27): "yellow",
}


def _palette_entries():
    return [
        {
            "id": color_id,
            "name": color_id,
            "name_zh": color_id,
            "hex": hex_value,
            "brand_code": None,
        }
        for color_id, hex_value in COLORS.items()
    ]


def _expected_cells():
    by_rgba = {
        tuple(bytes.fromhex(hex_value.removeprefix("#"))) + (255,): color_id
        for color_id, hex_value in COLORS.items()
    }
    with Image.open(FIXTURE) as opened:
        image = opened.convert("RGBA")
    left, top, right, bottom = GRID_BOX
    assert image.size == (right + DISPLAY_PADDING, bottom + DISPLAY_PADDING)
    assert all(
        image.getpixel(coordinate)[3] == 0
        for coordinate in ((0, 0), (image.width - 1, image.height - 1))
    )
    cells = []
    for row in range(GRID_SIZE[1]):
        cells.append(
            [
                None
                if image.getpixel(
                    (
                        left + column * CELL_SCALE + CELL_SCALE // 2,
                        top + row * CELL_SCALE + CELL_SCALE // 2,
                    )
                )[3]
                == 0
                else by_rgba[
                    image.getpixel(
                        (
                            left + column * CELL_SCALE + CELL_SCALE // 2,
                            top + row * CELL_SCALE + CELL_SCALE // 2,
                        )
                    )
                ]
                for column in range(GRID_SIZE[0])
            ]
        )
    return cells


def test_complex_logical_fixture_preserves_identity_features_through_exact_grid(
    tmp_path,
):
    expected = _expected_cells()
    assert sum(cell == "eye" for row in expected for cell in row) == 2
    for (column, row), color_id in FEATURES.items():
        assert expected[row][column] == color_id

    palette = tmp_path / "palette.json"
    palette.write_text(json.dumps(_palette_entries()), encoding="utf-8")
    output = tmp_path / "compiled"
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(FIXTURE),
            "--output-dir",
            str(output),
            "--classification",
            "pattern-draft",
            "--width",
            str(GRID_SIZE[0]),
            "--height",
            str(GRID_SIZE[1]),
            "--grid-box",
            ",".join(str(value) for value in GRID_BOX),
            "--palette",
            str(palette),
            "--colors",
            str(len(COLORS)),
            "--verification",
            "verified",
        ],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    pattern = json.loads((output / "pattern.json").read_text(encoding="utf-8"))
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))

    assert (pattern["width"], pattern["height"]) == GRID_SIZE
    assert pattern["cells"] == expected
    for (column, row), color_id in FEATURES.items():
        assert pattern["cells"][row][column] == color_id

    assert 700 <= pattern["total_beads"] <= 950
    assert pattern["total_beads"] == sum(pattern["color_counts"].values())
    assert pattern["total_beads"] == sum(
        cell is not None for row in expected for cell in row
    )
    assert pattern["board_layout"]["columns"] == 2
    assert pattern["board_layout"]["rows"] == 2
    assert report["board_decision"]["width"] == GRID_SIZE[0]
    assert report["board_decision"]["height"] == GRID_SIZE[1]
    assert report["cleanup_changes"] == []
