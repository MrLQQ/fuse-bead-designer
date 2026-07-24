"""Conservative recovery of provable nearest-neighbor logical grids."""

from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class GridSpec:
    """A recovered logical grid and the raster box that contains it."""

    width: int
    height: int
    box: tuple[int, int, int, int]
    source: str
    confidence: float


class AmbiguousGridError(ValueError):
    """Raised when raster evidence does not prove one logical grid."""


def recover_nearest_neighbor_grid(image: Image.Image) -> GridSpec:
    """Recover a grid only from exact, regular nearest-neighbor evidence.

    Every proposed logical boundary must be visible as a pixel transition in
    each axis.  This deliberately rejects repeated logical rows or columns:
    without declared dimensions, those rasters do not prove whether identical
    neighboring cells are one logical cell or several.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a Pillow Image")

    horizontal_scale = _supported_scale(image, axis="x")
    vertical_scale = _supported_scale(image, axis="y")
    if (
        horizontal_scale is None
        or vertical_scale is None
        or horizontal_scale != vertical_scale
        or horizontal_scale <= 1
    ):
        raise _ambiguous()

    scale = horizontal_scale
    raster_width, raster_height = image.size
    if raster_width % scale or raster_height % scale:
        raise _ambiguous()

    logical_size = (raster_width // scale, raster_height // scale)
    logical = image.resize(logical_size, Image.Resampling.NEAREST)
    reexpanded = logical.resize(image.size, Image.Resampling.NEAREST)
    if reexpanded.mode != image.mode or reexpanded.tobytes() != image.tobytes():
        raise _ambiguous()

    return GridSpec(
        width=logical_size[0],
        height=logical_size[1],
        box=(0, 0, raster_width, raster_height),
        source="nearest-neighbor",
        confidence=1.0,
    )


def _supported_scale(image: Image.Image, *, axis: str) -> int | None:
    width, height = image.size
    pixels = image.load()
    length = width if axis == "x" else height
    cross_length = height if axis == "x" else width
    transitions: list[int] = []

    for boundary in range(1, length):
        if any(
            (
                pixels[boundary - 1, cross] != pixels[boundary, cross]
                if axis == "x"
                else pixels[cross, boundary - 1] != pixels[cross, boundary]
            )
            for cross in range(cross_length)
        ):
            transitions.append(boundary)

    if not transitions:
        return None
    scale = transitions[0]
    if scale <= 0 or transitions != list(range(scale, length, scale)):
        return None
    return scale


def _ambiguous() -> AmbiguousGridError:
    return AmbiguousGridError(
        "logical grid is ambiguous; declare explicit logical width and height"
    )
