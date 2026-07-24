"""Conservative recovery of provable nearest-neighbor logical grids."""

from dataclasses import dataclass
from math import gcd, isqrt

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

    Every nontrivial integer scale that divides both raster dimensions is
    tested. Exactly one scale must reproduce the raster byte-for-byte after
    nearest-neighbor reduction and re-expansion.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a Pillow Image")

    if not _has_transition(image):
        raise _ambiguous()

    candidates = _valid_scale_candidates(image)
    if len(candidates) != 1:
        raise _ambiguous()

    scale, logical = candidates[0]
    if not _axis_supports_scale(image, scale, axis="x") or not _axis_supports_scale(
        image, scale, axis="y"
    ):
        raise _ambiguous()
    raster_width, raster_height = image.size
    logical_size = logical.size

    return GridSpec(
        width=logical_size[0],
        height=logical_size[1],
        box=(0, 0, raster_width, raster_height),
        source="nearest-neighbor",
        confidence=1.0,
    )


def _has_transition(image: Image.Image) -> bool:
    width, height = image.size
    if width == 0 or height == 0:
        return False
    pixels = image.load()
    return any(
        (x > 0 and pixels[x - 1, y] != pixels[x, y])
        or (y > 0 and pixels[x, y - 1] != pixels[x, y])
        for y in range(height)
        for x in range(width)
    )


def _valid_scale_candidates(image: Image.Image) -> list[tuple[int, Image.Image]]:
    width, height = image.size
    source_bytes = image.tobytes()
    candidates: list[tuple[int, Image.Image]] = []
    for scale in _nontrivial_divisors(gcd(width, height)):
        logical = image.resize((width // scale, height // scale), Image.Resampling.NEAREST)
        reexpanded = logical.resize(image.size, Image.Resampling.NEAREST)
        if reexpanded.mode == image.mode and reexpanded.tobytes() == source_bytes:
            candidates.append((scale, logical))
    return candidates


def _axis_supports_scale(image: Image.Image, scale: int, *, axis: str) -> bool:
    width, height = image.size
    pixels = image.load()
    length = width if axis == "x" else height
    cross_length = height if axis == "x" else width
    transitions = [
        boundary
        for boundary in range(1, length)
        if any(
            (
                pixels[boundary - 1, cross] != pixels[boundary, cross]
                if axis == "x"
                else pixels[cross, boundary - 1] != pixels[cross, boundary]
            )
            for cross in range(cross_length)
        )
    ]
    return transitions == list(range(scale, length, scale))


def _nontrivial_divisors(value: int) -> list[int]:
    divisors: set[int] = set()
    for divisor in range(2, isqrt(value) + 1):
        if value % divisor == 0:
            divisors.add(divisor)
            divisors.add(value // divisor)
    if value > 1:
        divisors.add(value)
    return sorted(divisors)


def _ambiguous() -> AmbiguousGridError:
    return AmbiguousGridError(
        "logical grid is ambiguous; declare explicit logical width and height"
    )
