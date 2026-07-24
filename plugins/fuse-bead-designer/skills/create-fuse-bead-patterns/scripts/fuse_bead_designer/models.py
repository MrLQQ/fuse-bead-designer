from collections import Counter
from dataclasses import asdict, dataclass, field
from enum import Enum


class VerificationState(str, Enum):
    VERIFIED = "verified"
    INFERRED_LOW = "inferred-low"
    REVIEW_REQUIRED = "review-required"


@dataclass(frozen=True)
class PaletteColor:
    id: str
    name: str
    name_zh: str
    hex: str
    brand_code: str | None = None


@dataclass
class Pattern:
    width: int
    height: int
    module_size: int
    palette: list[PaletteColor]
    cells: list[list[str | None]]
    verification: VerificationState
    board_columns: int = 1
    board_rows: int = 1
    is_custom_size: bool = False
    inferred_cells: list[tuple[int, int]] = field(default_factory=list)
    settings: dict[str, object] = field(default_factory=dict)

    def validate(self) -> None:
        if not _are_integers(self.width, self.height):
            raise ValueError("grid dimensions must be integers")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("grid dimensions must be positive")
        if not _is_integer(self.module_size):
            raise ValueError("module size must be an integer")
        if self.module_size <= 0:
            raise ValueError("module size must be positive")
        if not _are_integers(self.board_columns, self.board_rows):
            raise ValueError("board layout dimensions must be integers")
        if self.board_columns <= 0 or self.board_rows <= 0:
            raise ValueError("board layout dimensions must be positive")
        if not isinstance(self.is_custom_size, bool):
            raise ValueError("is_custom_size must be a boolean")
        if not isinstance(self.verification, VerificationState):
            raise ValueError("verification must be a VerificationState")
        if not isinstance(self.settings, dict):
            raise ValueError("settings must be an object")
        if not self.is_custom_size and (
            self.width != 29 * self.board_columns
            or self.height != 29 * self.board_rows
        ):
            raise ValueError("standard board layout dimensions do not match 29-module layout")
        if not isinstance(self.cells, list):
            raise ValueError("cells must be a list of rows")
        if any(not isinstance(row, list) for row in self.cells):
            raise ValueError("cell rows must be lists")
        if len(self.cells) != self.height:
            raise ValueError("cell row count does not match height")
        if any(len(row) != self.width for row in self.cells):
            raise ValueError("cell column count does not match width")
        if any(
            cell is not None and not isinstance(cell, str)
            for row in self.cells
            for cell in row
        ):
            raise ValueError("cell value must be a palette id string or None")
        if not isinstance(self.palette, list):
            raise ValueError("palette must be a list")
        if any(not isinstance(color, PaletteColor) for color in self.palette):
            raise ValueError("palette entries must be PaletteColor instances")
        for color in self.palette:
            _validate_palette_color(color)
        palette_ids = [color.id for color in self.palette]
        if len(palette_ids) != len(set(palette_ids)):
            raise ValueError("duplicate palette id")
        known = set(palette_ids)
        for row in self.cells:
            for cell in row:
                if cell is not None and cell not in known:
                    raise ValueError(f"unknown palette id: {cell}")
        if not isinstance(self.inferred_cells, list):
            raise ValueError("inferred_cells must be a list")
        for cell in self.inferred_cells:
            if not isinstance(cell, (list, tuple)) or len(cell) != 2:
                raise ValueError("inferred cell must be a coordinate pair")
            column, row = cell
            if not _are_integers(column, row):
                raise ValueError("inferred cell coordinates must be integers")
            if not (0 <= column < self.width and 0 <= row < self.height):
                raise ValueError("inferred cell is outside the grid")

    def color_counts(self) -> dict[str, int]:
        self.validate()
        counts = Counter(cell for row in self.cells for cell in row if cell is not None)
        return dict(sorted(counts.items()))

    @property
    def total_beads(self) -> int:
        return sum(self.color_counts().values())

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "schema_version": 1,
            "width": self.width,
            "height": self.height,
            "module_size": self.module_size,
            "board_layout": {
                "columns": self.board_columns,
                "rows": self.board_rows,
                "is_custom_size": self.is_custom_size,
            },
            "palette": [asdict(color) for color in self.palette],
            "cells": self.cells,
            "total_beads": self.total_beads,
            "color_counts": self.color_counts(),
            "verification": self.verification.value,
            "inferred_cells": [list(cell) for cell in self.inferred_cells],
            "settings": self.settings,
        }


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _are_integers(*values: object) -> bool:
    return all(_is_integer(value) for value in values)


def _validate_palette_color(color: PaletteColor) -> None:
    for field_name in ("id", "name", "name_zh", "hex"):
        if not isinstance(getattr(color, field_name), str):
            raise ValueError(f"palette color {field_name} has an invalid type")
    if color.brand_code is not None and not isinstance(color.brand_code, str):
        raise ValueError("palette color brand_code has an invalid type")


@dataclass
class CompileReport:
    classification: str
    removed_interference: list[str]
    board_decision: dict[str, object]
    palette_decision: dict[str, object]
    cleanup_changes: list[tuple[int, int]]
    warnings: list[str]
    verification: VerificationState
    inferred_cells: list[tuple[int, int]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "classification": self.classification,
            "removed_interference": self.removed_interference,
            "board_decision": self.board_decision,
            "palette_decision": self.palette_decision,
            "cleanup_changes": [list(cell) for cell in self.cleanup_changes],
            "inferred_cells": [list(cell) for cell in self.inferred_cells],
            "warnings": self.warnings,
            "verification": self.verification.value,
        }
