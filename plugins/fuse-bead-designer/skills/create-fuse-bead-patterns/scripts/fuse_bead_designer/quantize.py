"""Deterministic image-to-cell palette quantization without dithering."""

from collections import Counter
from dataclasses import dataclass, replace
from math import isfinite
from statistics import median

from PIL import Image

from .models import PaletteColor
from .palettes import nearest_color


@dataclass(frozen=True)
class SampledCell:
    """One output-grid cell and the confidence of its palette assignment.

    ``distance`` is the CIE Lab distance returned by :func:`nearest_color`.
    Empty cells always have ``None`` for all color-derived fields.
    """

    occupied: bool
    color_id: str | None = None
    distance: float | None = None
    source_rgb: tuple[float, float, float] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.occupied, bool):
            raise ValueError("occupied must be a boolean")
        if not self.occupied:
            if any(value is not None for value in (self.color_id, self.distance, self.source_rgb)):
                raise ValueError("empty cells cannot contain color data")
            return
        if not isinstance(self.color_id, str) or not self.color_id:
            raise ValueError("occupied cells require a color id")
        if (
            isinstance(self.distance, bool)
            or not isinstance(self.distance, (int, float))
            or not isfinite(self.distance)
            or self.distance < 0
        ):
            raise ValueError("occupied cells require a finite non-negative distance")
        if self.source_rgb is not None and (
            not isinstance(self.source_rgb, tuple)
            or len(self.source_rgb) != 3
            or any(not isinstance(channel, (int, float)) or isinstance(channel, bool) for channel in self.source_rgb)
        ):
            raise ValueError("source_rgb must contain three numeric channels")


def sample_cells(
    image: Image.Image,
    mask: Image.Image,
    width: int,
    height: int,
    palette: list[PaletteColor],
    *,
    color_limit: int = 16,
) -> list[list[SampledCell]]:
    """Sample *image* into a row-major grid of palette-assigned cells.

    Every source pixel belongs to exactly one output rectangle.  A cell is
    occupied when non-zero mask coverage reaches 50 percent; its color comes
    only from those occupied source pixels.  Sampling each rectangle
    independently intentionally leaves no error-diffusion path between cells.
    """
    _validate_inputs(image, mask, width, height, palette, color_limit)
    rgb_image = image.convert("RGB")
    coverage_mask = mask.convert("L")
    image_width, image_height = rgb_image.size
    image_pixels = rgb_image.load()
    mask_pixels = coverage_mask.load()

    cells: list[list[SampledCell]] = []
    for row in range(height):
        top, bottom = _source_bounds(row, image_height, height)
        output_row: list[SampledCell] = []
        for column in range(width):
            left, right = _source_bounds(column, image_width, width)
            output_row.append(
                _sample_rectangle(image_pixels, mask_pixels, left, top, right, bottom, palette)
            )
        cells.append(output_row)
    return _limit_colors(cells, palette, color_limit)


def sample_cell_centers(
    image: Image.Image,
    mask: Image.Image,
    width: int,
    height: int,
    palette: list[PaletteColor],
    *,
    color_limit: int = 16,
    grid_box: tuple[int, int, int, int] | None = None,
) -> list[list[SampledCell]]:
    """Palette-map small center windows of declared logical cells.

    ``grid_box`` is the caller-declared grid extent.  The function never crops
    based on image or mask content, so empty edge cells remain part of the
    logical grid.
    """
    _validate_inputs(image, mask, width, height, palette, color_limit)
    left, top, right, bottom = _validate_grid_box(grid_box, image.size)
    _validate_center_sampling_geometry(left, top, right, bottom, width, height)
    rgb_image = image.convert("RGB")
    coverage_mask = mask.convert("L")
    image_pixels = rgb_image.load()
    mask_pixels = coverage_mask.load()

    cells: list[list[SampledCell]] = []
    for row in range(height):
        cell_top, cell_bottom = _source_bounds(row, bottom - top, height)
        output_row: list[SampledCell] = []
        for column in range(width):
            cell_left, cell_right = _source_bounds(column, right - left, width)
            sample_left, sample_right = _center_window(left + cell_left, left + cell_right)
            sample_top, sample_bottom = _center_window(top + cell_top, top + cell_bottom)
            output_row.append(
                _sample_rectangle(
                    image_pixels,
                    mask_pixels,
                    sample_left,
                    sample_top,
                    sample_right,
                    sample_bottom,
                    palette,
                )
            )
        cells.append(output_row)
    return _limit_colors(cells, palette, color_limit)


def _validate_inputs(
    image: object,
    mask: object,
    width: object,
    height: object,
    palette: object,
    color_limit: object,
) -> None:
    if not isinstance(image, Image.Image) or not isinstance(mask, Image.Image):
        raise TypeError("image and mask must be Pillow Images")
    if image.size != mask.size:
        raise ValueError("image and mask dimensions must match")
    for name, value in (("width", width), ("height", height)):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if not isinstance(color_limit, int) or isinstance(color_limit, bool) or color_limit <= 0:
        raise ValueError("color_limit must be a positive integer")
    if not isinstance(palette, list) or not palette:
        raise ValueError("palette must contain at least one color")
    if any(not isinstance(color, PaletteColor) for color in palette):
        raise ValueError("palette entries must be PaletteColor instances")
    if len({color.id for color in palette}) != len(palette):
        raise ValueError("duplicate palette id")


def _validate_grid_box(
    grid_box: object,
    image_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    if grid_box is None:
        return (0, 0, image_size[0], image_size[1])
    if (
        not isinstance(grid_box, tuple)
        or len(grid_box) != 4
        or any(not isinstance(value, int) or isinstance(value, bool) for value in grid_box)
    ):
        raise ValueError("grid_box must contain four integer coordinates")
    left, top, right, bottom = grid_box
    if left < 0 or top < 0 or right > image_size[0] or bottom > image_size[1]:
        raise ValueError("grid_box must be within image bounds")
    if left >= right or top >= bottom:
        raise ValueError("grid_box must have positive width and height")
    return grid_box


def _source_bounds(index: int, source_length: int, output_length: int) -> tuple[int, int]:
    return index * source_length // output_length, (index + 1) * source_length // output_length


def _validate_center_sampling_geometry(
    left: int,
    top: int,
    right: int,
    bottom: int,
    width: int,
    height: int,
) -> None:
    if right - left < width * 4 or bottom - top < height * 4:
        raise ValueError(
            "center sampling requires at least 4 source pixels per logical cell "
            "in each direction"
        )


def _center_window(start: int, end: int) -> tuple[int, int]:
    rectangle_length = end - start
    window_length = rectangle_length // 4
    if window_length % 2 == 0:
        window_length -= 1
    assert window_length >= 1
    window_start = start + (rectangle_length - window_length) // 2
    return window_start, window_start + window_length


def _sample_rectangle(
    image_pixels: object,
    mask_pixels: object,
    left: int,
    top: int,
    right: int,
    bottom: int,
    palette: list[PaletteColor],
) -> SampledCell:
    pixel_count = (right - left) * (bottom - top)
    if pixel_count == 0:
        return SampledCell(False)

    coverage = 0
    occupied_pixels: list[tuple[int, int, int]] = []
    for y in range(top, bottom):
        for x in range(left, right):
            mask_value = mask_pixels[x, y]
            coverage += mask_value
            if mask_value > 0:
                occupied_pixels.append(image_pixels[x, y])
    if coverage < 255 * pixel_count / 2:
        return SampledCell(False)

    source_rgb = tuple(float(median(channel)) for channel in zip(*occupied_pixels))
    match = nearest_color(tuple(round(channel) for channel in source_rgb), palette)
    return SampledCell(True, match.color_id, match.distance, source_rgb)


def _limit_colors(
    cells: list[list[SampledCell]],
    palette: list[PaletteColor],
    color_limit: int,
) -> list[list[SampledCell]]:
    counts = Counter(cell.color_id for row in cells for cell in row if cell.occupied)
    if len(counts) <= color_limit:
        return cells

    kept_ids = {
        color_id
        for color_id, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:color_limit]
    }
    kept_palette = [color for color in palette if color.id in kept_ids]
    limited: list[list[SampledCell]] = []
    for row in cells:
        limited_row: list[SampledCell] = []
        for cell in row:
            if not cell.occupied or cell.color_id in kept_ids:
                limited_row.append(cell)
                continue
            assert cell.source_rgb is not None
            match = nearest_color(tuple(round(channel) for channel in cell.source_rgb), kept_palette)
            limited_row.append(replace(cell, color_id=match.color_id, distance=match.distance))
        limited.append(limited_row)
    return limited
