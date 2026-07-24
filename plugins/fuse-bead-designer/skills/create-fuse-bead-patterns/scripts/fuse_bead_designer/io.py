"""Structured artifact writers for fuse-bead patterns."""

import csv
import json
import os
from pathlib import Path
import shutil
import tempfile

from .models import CompileReport, Pattern
from .render import render_review, render_template


CSV_COLUMNS = ("id", "name", "name_zh", "hex", "brand_code", "count")
GENERATED_ARTIFACTS = ("template.png", "pattern.json", "colors.csv", "report.json", "review.png")


def write_artifacts(
    pattern: Pattern,
    output_dir: str | Path,
    *,
    report: CompileReport | None = None,
) -> None:
    """Write count-consistent artifacts without exposing partial updates."""
    pattern.validate()
    _validate_report(pattern, report)
    destination = Path(output_dir)
    _validate_destination(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".fuse-bead-staging-", dir=destination.parent))
    try:
        _write_staged_artifacts(pattern, staging, report)
        destination.mkdir(exist_ok=True)
        _publish_staged_artifacts(staging, destination)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _write_staged_artifacts(
    pattern: Pattern, staging: Path, report: CompileReport | None
) -> None:
    _write_json(staging / "pattern.json", pattern.to_dict())
    _write_colors_csv(pattern, staging / "colors.csv")
    _write_json(staging / "report.json", _report_data(pattern, report))
    render_template(pattern).save(staging / "template.png")
    if pattern.inferred_cells or (report is not None and report.cleanup_changes):
        render_review(pattern, report).save(staging / "review.png")


def _validate_destination(destination: Path) -> None:
    if destination.exists() and not destination.is_dir():
        raise ValueError("output path must be a directory")
    for name in GENERATED_ARTIFACTS:
        target = destination / name
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError(f"generated artifact target is not a regular file: {name}")


def _publish_staged_artifacts(staging: Path, destination: Path) -> None:
    backup = Path(tempfile.mkdtemp(prefix=".fuse-bead-backup-", dir=destination.parent))
    moved_originals: list[str] = []
    published: list[str] = []
    try:
        for name in GENERATED_ARTIFACTS:
            target = destination / name
            if target.exists():
                os.replace(target, backup / name)
                moved_originals.append(name)
        for staged_artifact in staging.iterdir():
            os.replace(staged_artifact, destination / staged_artifact.name)
            published.append(staged_artifact.name)
    except OSError:
        for name in published:
            (destination / name).unlink(missing_ok=True)
        for name in moved_originals:
            os.replace(backup / name, destination / name)
        raise
    finally:
        shutil.rmtree(backup, ignore_errors=True)


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_colors_csv(pattern: Pattern, path: Path) -> None:
    counts = pattern.color_counts()
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for color in pattern.palette:
            writer.writerow(
                {
                    "id": color.id,
                    "name": color.name,
                    "name_zh": color.name_zh,
                    "hex": color.hex,
                    "brand_code": color.brand_code or "",
                    "count": counts.get(color.id, 0),
                }
            )


def _report_data(pattern: Pattern, report: CompileReport | None) -> dict[str, object]:
    if report is not None:
        return report.to_dict()
    return {
        "classification": "unreported",
        "removed_interference": [],
        "board_decision": {
            "columns": pattern.board_columns,
            "rows": pattern.board_rows,
            "is_custom_size": pattern.is_custom_size,
        },
        "palette_decision": {"color_ids": [color.id for color in pattern.palette]},
        "cleanup_changes": [],
        "inferred_cells": [list(cell) for cell in pattern.inferred_cells],
        "warnings": [],
        "verification": pattern.verification.value,
    }


def _validate_report(pattern: Pattern, report: CompileReport | None) -> None:
    if report is None:
        return
    _validate_coordinates(pattern, report.cleanup_changes, "cleanup change", "cleanup_changes")
    _validate_coordinates(pattern, report.inferred_cells, "inferred cell", "inferred_cells")
    if report.inferred_cells != pattern.inferred_cells:
        raise ValueError("report inferred cells must match pattern inferred cells")


def _validate_coordinates(
    pattern: Pattern, coordinates: object, label: str, field_name: str
) -> None:
    if not isinstance(coordinates, list):
        raise ValueError(f"{field_name} must be a list")
    for coordinate in coordinates:
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) != 2:
            raise ValueError(f"{label} must be a coordinate pair")
        column, row = coordinate
        if (
            not isinstance(column, int)
            or isinstance(column, bool)
            or not isinstance(row, int)
            or isinstance(row, bool)
        ):
            raise ValueError(f"{label} coordinates must be integers")
        if not (0 <= column < pattern.width and 0 <= row < pattern.height):
            raise ValueError(f"{label} is outside the grid")
