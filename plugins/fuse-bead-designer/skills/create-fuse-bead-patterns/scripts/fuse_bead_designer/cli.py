"""Command-line orchestration for deterministic fuse-bead compilation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from PIL import Image

from .boards import STANDARD_CANDIDATES, BoardSelection, layout_boards, select_board
from .cleanup import CleanupResult, cleanup_cells
from .io import write_artifacts
from .logical_grid import AmbiguousGridError, recover_nearest_neighbor_grid
from .masking import derive_subject_mask
from .models import CompileReport, Pattern, VerificationState
from .palettes import load_palette
from .quantize import sample_cell_centers, sample_cells
from .routing import policy_for


GENERATED_ARTIFACTS = frozenset(
    {"template.png", "pattern.json", "colors.csv", "report.json", "review.png"}
)
CLASSIFICATIONS = (
    "finished-bead-photo",
    "pixel-art",
    "pattern-draft",
    "high-resolution-image",
    "unclassified",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile a clean image subject into a count-accurate fuse-bead pattern."
    )
    parser.add_argument("--input", required=True, metavar="INPUT", help="clean subject image")
    parser.add_argument("--output-dir", required=True, metavar="DIR", help="artifact directory")
    parser.add_argument("--width", type=_positive_integer, metavar="CELLS")
    parser.add_argument("--height", type=_positive_integer, metavar="CELLS")
    parser.add_argument("--max-boards", type=_positive_integer, default=4, metavar="COUNT")
    parser.add_argument("--palette", metavar="PATH", help="JSON or CSV palette path")
    parser.add_argument("--colors", type=_color_limit, default=16, metavar="COUNT")
    parser.add_argument(
        "--verification",
        choices=[state.value for state in VerificationState],
        default=VerificationState.VERIFIED.value,
    )
    parser.add_argument(
        "--inferred-cells",
        action="append",
        nargs="+",
        default=[],
        metavar="COLUMN,ROW",
        help="one or more inferred coordinates",
    )
    parser.add_argument(
        "--protect-cells",
        action="append",
        nargs="+",
        default=[],
        metavar="COLUMN,ROW",
        help="one or more coordinates excluded from cleanup",
    )
    parser.add_argument(
        "--classification",
        choices=CLASSIFICATIONS,
        default="unclassified",
    )
    parser.add_argument("--rectified-grid", action="store_true")
    parser.add_argument("--draft-input", metavar="PATH")
    parser.add_argument("--grid-box", metavar="LEFT,TOP,RIGHT,BOTTOM")
    parser.add_argument("--sampling", choices=("center", "median"))
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--legacy-resample", action="store_true")
    parser.add_argument(
        "--removed-interference",
        action="append",
        nargs="+",
        default=[],
        metavar="DESCRIPTION",
        help="interference already removed from the clean input",
    )
    parser.add_argument(
        "--confirm-large-board",
        action="store_true",
        help="acknowledge a layout that needs more than four standard boards",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace generated artifacts in a non-empty output directory",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        arguments = parser.parse_args(argv)
        _validate_paired_size(arguments, parser)
        arguments.route_policy = policy_for(
            arguments.classification,
            rectified_grid=arguments.rectified_grid,
            has_pattern_draft=arguments.draft_input is not None,
            legacy_resample=arguments.legacy_resample,
        )
        inferred_cells = _parse_coordinates(arguments.inferred_cells)
        _validate_verification_for_route(arguments, inferred_cells)
        arguments.sampling = arguments.sampling or arguments.route_policy.sampling
        arguments.cleanup = arguments.cleanup or arguments.route_policy.cleanup
        output_dir = Path(arguments.output_dir)
        _validate_output_dir(output_dir, arguments.force)

        protected_cells = _parse_coordinates(arguments.protect_cells)
        palette = load_palette(arguments.palette)
        exact_route = (
            arguments.classification != "unclassified"
            and not arguments.legacy_resample
        )
        source_path = Path(arguments.input)
        draft_path = Path(arguments.draft_input) if arguments.draft_input else None
        draft_used = (
            exact_route
            and arguments.classification == "high-resolution-image"
            and draft_path is not None
        )
        compiled_path = draft_path if draft_used else source_path
        assert compiled_path is not None
        if draft_used:
            _open_image(source_path)
        image = _open_image(compiled_path)
        arguments.grid_box = _parse_grid_box(arguments.grid_box, image.size)
        grid_box = arguments.grid_box
        grid_evidence: dict[str, object]
        if exact_route:
            if arguments.width is not None:
                selection = _exact_selection(arguments.width, arguments.height)
                grid_evidence = {
                    "source": "declared",
                    "confidence": 1.0,
                    "width": selection.width,
                    "height": selection.height,
                    "box": list(grid_box or (0, 0, image.width, image.height)),
                }
            else:
                recovery_image = image.crop(grid_box) if grid_box is not None else image
                try:
                    recovered = recover_nearest_neighbor_grid(recovery_image)
                except AmbiguousGridError as error:
                    raise ValueError(
                        "logical grid is ambiguous; provide --width and --height"
                    ) from error
                selection = _exact_selection(recovered.width, recovered.height)
                if grid_box is None:
                    grid_box = recovered.box
                grid_evidence = {
                    "source": recovered.source,
                    "confidence": recovered.confidence,
                    "width": recovered.width,
                    "height": recovered.height,
                    "box": list(grid_box),
                }
        else:
            selection = select_board(
                image.width,
                image.height,
                explicit_size=(arguments.width, arguments.height)
                if arguments.width is not None
                else None,
                max_boards=arguments.max_boards,
            )
            grid_evidence = {
                "source": "legacy-board-selection",
                "confidence": None,
                "width": selection.width,
                "height": selection.height,
                "box": None,
            }
        _validate_coordinates_in_bounds(inferred_cells, selection)
        _validate_coordinates_in_bounds(protected_cells, selection)
        if selection.requires_confirmation and not arguments.confirm_large_board:
            raise ValueError("more than four boards requires --confirm-large-board")

        mask = derive_subject_mask(image)
        if exact_route and arguments.sampling == "center":
            sampled_cells = sample_cell_centers(
                image,
                mask,
                selection.width,
                selection.height,
                palette,
                color_limit=arguments.colors,
                grid_box=grid_box,
            )
        elif exact_route:
            median_image = image.crop(grid_box) if grid_box is not None else image
            median_mask = mask.crop(grid_box) if grid_box is not None else mask
            sampled_cells = sample_cells(
                median_image,
                median_mask,
                selection.width,
                selection.height,
                palette,
                color_limit=arguments.colors,
            )
        else:
            sampled_cells = sample_cells(
                image,
                mask,
                selection.width,
                selection.height,
                palette,
                color_limit=arguments.colors,
            )
        cleanup = (
            cleanup_cells(sampled_cells, protected_cells=frozenset(protected_cells))
            if arguments.cleanup
            else CleanupResult(sampled_cells, [])
        )
        pattern = Pattern(
            width=selection.width,
            height=selection.height,
            module_size=29,
            palette=palette,
            cells=[
                [cell.color_id if cell.occupied else None for cell in row]
                for row in cleanup.cells
            ],
            verification=VerificationState(arguments.verification),
            board_columns=selection.board_columns,
            board_rows=selection.board_rows,
            is_custom_size=selection.is_custom,
            inferred_cells=inferred_cells,
            settings={
                "colors": arguments.colors,
                "max_boards": arguments.max_boards,
                "source_classification": arguments.classification,
                "sampling": arguments.sampling,
                "cleanup": arguments.cleanup,
                "grid_box": list(grid_box) if grid_box is not None else None,
                "draft_used": draft_used,
                "grid_evidence": grid_evidence,
                "source_input": str(source_path),
                "draft_input": str(draft_path) if draft_path is not None else None,
                "compiled_input": str(compiled_path),
                "protected_cells": [list(cell) for cell in protected_cells],
            },
        )
        report = CompileReport(
            classification=arguments.classification,
            removed_interference=_flatten(arguments.removed_interference),
            board_decision=_board_decision(selection),
            palette_decision={
                "source": str(Path(arguments.palette)) if arguments.palette else "generic",
                "color_limit": arguments.colors,
                "color_ids": [color.id for color in palette],
            },
            cleanup_changes=cleanup.changed_cells,
            warnings=_warnings(selection, pattern.verification),
            verification=pattern.verification,
            inferred_cells=inferred_cells,
            source_classification=arguments.classification,
            sampling=arguments.sampling,
            cleanup=arguments.cleanup,
            grid_box=grid_box,
            draft_used=draft_used,
            grid_evidence=grid_evidence,
            source_input=str(source_path),
            draft_input=str(draft_path) if draft_path is not None else None,
            compiled_input=str(compiled_path),
        )
        write_artifacts(pattern, output_dir, report=report)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 0


def _positive_integer(value: str) -> int:
    try:
        result = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if result <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return result


def _exact_selection(width: int, height: int) -> BoardSelection:
    layout = layout_boards(width, height)
    return BoardSelection(
        width=layout.pattern_width,
        height=layout.pattern_height,
        board_columns=layout.board_columns,
        board_rows=layout.board_rows,
        is_custom=(width, height) not in STANDARD_CANDIDATES,
        requires_confirmation=layout.board_columns * layout.board_rows > 4,
        score=0.0,
        alternatives=(),
    )


def _color_limit(value: str) -> int:
    try:
        result = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("--colors must be an integer from 8 through 16") from error
    if not 8 <= result <= 16:
        raise argparse.ArgumentTypeError("--colors must be an integer from 8 through 16")
    return result


def _validate_paired_size(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if (arguments.width is None) != (arguments.height is None):
        parser.error("--width and --height must be provided together")


def _validate_verification_for_route(
    arguments: argparse.Namespace,
    inferred_cells: list[tuple[int, int]],
) -> None:
    if (
        inferred_cells
        and arguments.verification == VerificationState.VERIFIED.value
    ):
        raise ValueError(
            "inferred cells require inferred-low or review-required verification"
        )
    if (
        arguments.classification == "high-resolution-image"
        and arguments.verification == VerificationState.VERIFIED.value
    ):
        raise ValueError(
            "high-resolution-image requires inferred-low or review-required "
            "verification"
        )


def _validate_output_dir(output_dir: Path, force: bool) -> None:
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("output path must be a directory")
    if output_dir.is_dir() and any(output_dir.iterdir()) and not force:
        raise ValueError("refusing to overwrite a non-empty output directory without --force")


def _parse_coordinates(groups: list[list[str]]) -> list[tuple[int, int]]:
    return [_parse_coordinate(value) for value in _flatten(groups)]


def _parse_coordinate(value: str) -> tuple[int, int]:
    parts = value.split(",")
    if len(parts) != 2:
        raise ValueError("coordinates must use column,row")
    try:
        column, row = (int(part) for part in parts)
    except ValueError as error:
        raise ValueError("coordinates must use column,row") from error
    if column < 0 or row < 0:
        raise ValueError("coordinates must use non-negative column,row")
    return column, row


def _parse_grid_box(
    value: str | None, image_size: tuple[int, int]
) -> tuple[int, int, int, int] | None:
    if value is None:
        return None
    parts = value.split(",")
    if len(parts) != 4:
        raise ValueError("grid box must use left,top,right,bottom")
    try:
        left, top, right, bottom = (int(part) for part in parts)
    except ValueError as error:
        raise ValueError("grid box must use four integer coordinates") from error
    image_width, image_height = image_size
    if left < 0 or top < 0 or right > image_width or bottom > image_height:
        raise ValueError("grid box must be within image bounds")
    if right <= left or bottom <= top:
        raise ValueError("grid box must have positive width and height")
    return left, top, right, bottom


def _validate_coordinates_in_bounds(
    coordinates: list[tuple[int, int]], selection: BoardSelection
) -> None:
    for column, row in coordinates:
        if not (0 <= column < selection.width and 0 <= row < selection.height):
            raise ValueError("coordinate is outside the selected grid")


def _open_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        source.load()
        return source.copy()


def _flatten(groups: list[list[str]]) -> list[str]:
    return [item for group in groups for item in group]


def _board_decision(selection: BoardSelection) -> dict[str, object]:
    return {
        "width": selection.width,
        "height": selection.height,
        "columns": selection.board_columns,
        "rows": selection.board_rows,
        "is_custom_size": selection.is_custom,
        "score": selection.score,
        "alternatives": [list(size) for size in selection.alternatives],
    }


def _warnings(selection: BoardSelection, verification: VerificationState) -> list[str]:
    warnings: list[str] = []
    if selection.alternatives:
        warnings.append("Close board-size alternatives are available for review.")
    if verification is VerificationState.REVIEW_REQUIRED:
        warnings.append("Quantities are provisional until review is confirmed.")
    return warnings
