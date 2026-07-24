"""Structured artifact writers for fuse-bead patterns."""

import csv
import json
from pathlib import Path

from .models import CompileReport, Pattern
from .render import render_review, render_template


CSV_COLUMNS = ("id", "name", "name_zh", "hex", "brand_code", "count")


def write_artifacts(
    pattern: Pattern,
    output_dir: str | Path,
    *,
    report: CompileReport | None = None,
) -> None:
    """Write count-consistent image, JSON, CSV, report, and conditional review PNG."""
    pattern.validate()
    _validate_cleanup_changes(pattern, report)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    review_path = destination / "review.png"
    _write_json(destination / "pattern.json", pattern.to_dict())
    _write_colors_csv(pattern, destination / "colors.csv")
    _write_json(destination / "report.json", _report_data(pattern, report))
    render_template(pattern).save(destination / "template.png")
    if pattern.inferred_cells or (report is not None and report.cleanup_changes):
        render_review(pattern, report).save(review_path)
    else:
        review_path.unlink(missing_ok=True)


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
        "warnings": [],
        "verification": pattern.verification.value,
    }


def _validate_cleanup_changes(pattern: Pattern, report: CompileReport | None) -> None:
    if report is None:
        return
    if not isinstance(report.cleanup_changes, list):
        raise ValueError("cleanup_changes must be a list")
    for change in report.cleanup_changes:
        if not isinstance(change, (list, tuple)) or len(change) != 2:
            raise ValueError("cleanup change must be a coordinate pair")
        column, row = change
        if (
            not isinstance(column, int)
            or isinstance(column, bool)
            or not isinstance(row, int)
            or isinstance(row, bool)
        ):
            raise ValueError("cleanup change coordinates must be integers")
        if not (0 <= column < pattern.width and 0 <= row < pattern.height):
            raise ValueError("cleanup change is outside the grid")
