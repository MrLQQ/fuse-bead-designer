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
        if self.width <= 0 or self.height <= 0:
            raise ValueError("grid dimensions must be positive")
        if self.board_columns <= 0 or self.board_rows <= 0:
            raise ValueError("board layout dimensions must be positive")
        if not self.is_custom_size and (
            self.width != 29 * self.board_columns
            or self.height != 29 * self.board_rows
        ):
            raise ValueError("standard board layout dimensions do not match 29-module layout")
        if len(self.cells) != self.height:
            raise ValueError("cell row count does not match height")
        if any(len(row) != self.width for row in self.cells):
            raise ValueError("cell column count does not match width")
        palette_ids = [color.id for color in self.palette]
        if len(palette_ids) != len(set(palette_ids)):
            raise ValueError("duplicate palette id")
        known = set(palette_ids)
        for row in self.cells:
            for cell in row:
                if cell is not None and cell not in known:
                    raise ValueError(f"unknown palette id: {cell}")
        for column, row in self.inferred_cells:
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


@dataclass
class CompileReport:
    classification: str
    removed_interference: list[str]
    board_decision: dict[str, object]
    palette_decision: dict[str, object]
    cleanup_changes: list[tuple[int, int]]
    warnings: list[str]
    verification: VerificationState

    def to_dict(self) -> dict[str, object]:
        return {
            "classification": self.classification,
            "removed_interference": self.removed_interference,
            "board_decision": self.board_decision,
            "palette_decision": self.palette_decision,
            "cleanup_changes": [list(cell) for cell in self.cleanup_changes],
            "warnings": self.warnings,
            "verification": self.verification.value,
        }
