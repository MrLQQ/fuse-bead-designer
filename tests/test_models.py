import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from fuse_bead_designer.models import (
    CompileReport,
    PaletteColor,
    Pattern,
    VerificationState,
)


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
    [(28, 29, 2, 1), (29, 28, 1, 2), (58, 29, 1, 1), (29, 58, 1, 1)],
)
def test_pattern_requires_board_layout_to_match_module_size_coverage(
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

    with pytest.raises(ValueError, match="board layout dimensions"):
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


@pytest.mark.parametrize("module_size", [0, -1])
def test_pattern_rejects_non_positive_module_size(module_size):
    pattern = valid_pattern(module_size=module_size)

    with pytest.raises(ValueError, match="module size must be positive"):
        pattern.validate()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("width", True, "grid dimensions must be integers"),
        ("height", 29.0, "grid dimensions must be integers"),
        ("module_size", "29", "module size must be an integer"),
        ("board_columns", True, "board layout dimensions must be integers"),
        ("board_rows", 1.0, "board layout dimensions must be integers"),
        ("is_custom_size", 1, "is_custom_size must be a boolean"),
        ("verification", "verified", "verification must be a VerificationState"),
        ("settings", [], "settings must be an object"),
    ],
)
def test_pattern_rejects_schema_incompatible_scalar_field_types(field, value, message):
    pattern = valid_pattern(**{field: value})

    with pytest.raises(ValueError, match=message):
        pattern.validate()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", 1),
        ("name", 1),
        ("name_zh", 1),
        ("hex", 1),
        ("brand_code", 1),
    ],
)
def test_pattern_rejects_palette_color_with_schema_incompatible_field(field, value):
    values = {
        "id": "red",
        "name": "Red",
        "name_zh": "红色",
        "hex": "#FF0000",
        "brand_code": None,
    }
    values[field] = value
    pattern = valid_pattern(palette=[PaletteColor(**values)])

    with pytest.raises(ValueError, match=f"palette color {field} has an invalid type"):
        pattern.validate()


def test_pattern_rejects_non_palette_color_entry():
    pattern = valid_pattern(palette=["red"])

    with pytest.raises(ValueError, match="palette entries must be PaletteColor instances"):
        pattern.validate()


@pytest.mark.parametrize(
    ("cells", "message"),
    [
        ("not rows", "cells must be a list of rows"),
        ([[None] * 29 for _ in range(28)] + [tuple([None] * 29)], "cell rows must be lists"),
        ([[None] * 28 + [1] for _ in range(29)], "cell value must be a palette id string or None"),
    ],
)
def test_pattern_rejects_schema_incompatible_cells(cells, message):
    pattern = valid_pattern(cells=cells)

    with pytest.raises(ValueError, match=message):
        pattern.validate()


@pytest.mark.parametrize(
    ("inferred_cells", "message"),
    [
        ("not coordinates", "inferred_cells must be a list"),
        ([(0, 0, 0)], "inferred cell must be a coordinate pair"),
        ([(True, 0)], "inferred cell coordinates must be integers"),
        ([(0, "0")], "inferred cell coordinates must be integers"),
    ],
)
def test_pattern_rejects_schema_incompatible_inferred_cells(inferred_cells, message):
    pattern = valid_pattern(inferred_cells=inferred_cells)

    with pytest.raises(ValueError, match=message):
        pattern.validate()


def test_valid_pattern_serialization_round_trips_against_json_schema():
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

    Draft202012Validator(schema).validate(valid_pattern().to_dict())


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


def test_compile_report_serializes_exact_route_provenance_without_renaming_legacy_keys():
    report = CompileReport(
        classification="pixel-art",
        removed_interference=[],
        board_decision={"columns": 3, "rows": 3},
        palette_decision={"source": "generic"},
        cleanup_changes=[],
        warnings=[],
        verification=VerificationState.VERIFIED,
        source_classification="pixel-art",
        sampling="center",
        cleanup=False,
        grid_box=(4, 8, 276, 248),
        draft_used=False,
        grid_evidence={
            "source": "declared",
            "confidence": 1.0,
            "width": 68,
            "height": 60,
        },
        source_input="source.png",
        compiled_input="source.png",
        fidelity={
            "grid": {"status": "declared"},
            "color": {"status": "exact"},
            "semantic": {"status": "verified"},
        },
    )

    data = report.to_dict()

    assert data["classification"] == "pixel-art"
    assert data["board_decision"] == {"columns": 3, "rows": 3}
    assert data["source_classification"] == "pixel-art"
    assert data["sampling"] == "center"
    assert data["cleanup"] is False
    assert data["grid_box"] == [4, 8, 276, 248]
    assert data["draft_used"] is False
    assert data["grid_evidence"]["source"] == "declared"
    assert data["source_input"] == data["compiled_input"] == "source.png"
    assert data["fidelity"] == {
        "grid": {"status": "declared"},
        "color": {"status": "exact"},
        "semantic": {"status": "verified"},
    }
