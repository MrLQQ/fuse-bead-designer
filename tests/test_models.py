import json
from pathlib import Path

import pytest

from fuse_bead_designer.models import PaletteColor, Pattern, VerificationState


def valid_pattern(**changes):
    values = {
        "width": 29,
        "height": 29,
        "module_size": 29,
        "palette": [PaletteColor("red", "Red", "红色", "#FF0000")],
        "cells": [[None] * 29 for _ in range(29)],
        "verification": VerificationState.VERIFIED,
    }
    values.update(changes)
    return Pattern(**values)


def test_white_bead_is_distinct_from_empty_cell():
    pattern = Pattern(
        width=2,
        height=1,
        module_size=29,
        palette=[PaletteColor("white", "White", "白色", "#F7F4EA")],
        cells=[[None, "white"]],
        verification=VerificationState.VERIFIED,
        is_custom_size=True,
    )

    assert pattern.color_counts() == {"white": 1}
    assert pattern.total_beads == 1
    assert pattern.to_dict()["cells"] == [[None, "white"]]


def test_pattern_rejects_unknown_palette_identifier():
    pattern = Pattern(
        width=1,
        height=1,
        module_size=29,
        palette=[],
        cells=[["missing"]],
        verification=VerificationState.VERIFIED,
        is_custom_size=True,
    )

    with pytest.raises(ValueError, match="unknown palette id"):
        pattern.validate()


@pytest.mark.parametrize(
    ("width", "height"),
    [(0, 1), (1, 0), (-1, 1), (1, -1)],
)
def test_pattern_rejects_non_positive_grid_dimensions(width, height):
    pattern = valid_pattern(width=width, height=height)

    with pytest.raises(ValueError, match="grid dimensions must be positive"):
        pattern.validate()


def test_pattern_rejects_cell_row_count_that_does_not_match_height():
    pattern = valid_pattern(cells=[])

    with pytest.raises(ValueError, match="cell row count does not match height"):
        pattern.validate()


def test_pattern_rejects_cell_column_count_that_does_not_match_width():
    pattern = valid_pattern(cells=[[None] * 28 for _ in range(29)])

    with pytest.raises(ValueError, match="cell column count does not match width"):
        pattern.validate()


def test_pattern_rejects_duplicate_palette_ids():
    red = PaletteColor("red", "Red", "红色", "#FF0000")
    pattern = valid_pattern(palette=[red, red])

    with pytest.raises(ValueError, match="duplicate palette id"):
        pattern.validate()


@pytest.mark.parametrize("inferred_cell", [(-1, 0), (0, -1), (29, 0), (0, 29)])
def test_pattern_rejects_inferred_cell_outside_grid(inferred_cell):
    pattern = valid_pattern(inferred_cells=[inferred_cell])

    with pytest.raises(ValueError, match="inferred cell is outside the grid"):
        pattern.validate()


@pytest.mark.parametrize(
    ("board_columns", "board_rows"),
    [(0, 1), (1, 0), (-1, 1), (1, -1)],
)
def test_pattern_rejects_non_positive_board_layout(board_columns, board_rows):
    pattern = valid_pattern(
        board_columns=board_columns,
        board_rows=board_rows,
    )

    with pytest.raises(ValueError, match="board layout dimensions must be positive"):
        pattern.validate()


@pytest.mark.parametrize(
    ("width", "height", "board_columns", "board_rows"),
    [(28, 29, 1, 1), (29, 28, 1, 1), (58, 29, 1, 1), (29, 58, 1, 1)],
)
def test_standard_pattern_requires_matching_29_module_board_layout(
    width, height, board_columns, board_rows
):
    pattern = valid_pattern(
        width=width,
        height=height,
        board_columns=board_columns,
        board_rows=board_rows,
        is_custom_size=False,
        cells=[[None] * width for _ in range(height)],
    )

    with pytest.raises(ValueError, match="standard board layout dimensions"):
        pattern.validate()


def test_custom_size_pattern_does_not_require_standard_board_dimensions():
    pattern = Pattern(
        width=2,
        height=1,
        module_size=29,
        palette=[],
        cells=[[None, None]],
        verification=VerificationState.VERIFIED,
        is_custom_size=True,
    )

    pattern.validate()


def test_pattern_dict_has_schema_version_one():
    assert valid_pattern().to_dict()["schema_version"] == 1


def test_pattern_schema_defines_required_canonical_fields():
    schema_path = (
        Path(__file__).resolve().parents[1]
        / "plugins"
        / "fuse-bead-designer"
        / "skills"
        / "create-fuse-bead-patterns"
        / "assets"
        / "pattern.schema.json"
    )

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert set(schema["required"]) == {
        "schema_version",
        "width",
        "height",
        "module_size",
        "board_layout",
        "palette",
        "cells",
        "total_beads",
        "color_counts",
        "verification",
        "inferred_cells",
        "settings",
    }
    assert schema["properties"]["schema_version"] == {"const": 1}
    assert schema["properties"]["verification"]["enum"] == [
        "verified",
        "inferred-low",
        "review-required",
    ]
    assert schema["properties"]["cells"]["items"]["items"]["type"] == [
        "string",
        "null",
    ]
