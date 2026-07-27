from PIL import Image
import pytest

from fuse_bead_designer.logical_grid import (
    AmbiguousGridError,
    recover_nearest_neighbor_grid,
)


def _checkerboard(width: int, height: int) -> Image.Image:
    image = Image.new("RGB", (width, height))
    image.putdata(
        [
            (17, 21, 21) if (x + y) % 2 == 0 else (229, 57, 53)
            for y in range(height)
            for x in range(width)
        ]
    )
    return image


def test_recovers_provable_integer_nearest_neighbor_grid():
    logical = _checkerboard(16, 16)
    display = logical.resize((80, 80), Image.Resampling.NEAREST)

    spec = recover_nearest_neighbor_grid(display)

    assert (spec.width, spec.height) == logical.size
    assert spec.box == (0, 0, 80, 80)
    assert spec.source == "nearest-neighbor"
    assert spec.confidence == 1.0
    assert spec.scale == 5
    assert spec.area_factor == 25


@pytest.mark.parametrize(
    "image",
    [
        Image.new("RGB", (16, 16), "#111515"),
        _checkerboard(8, 8),
        _checkerboard(4, 4).resize((16, 16), Image.Resampling.BILINEAR),
    ],
    ids=["uniform", "scale-one", "anti-aliased"],
)
def test_recovery_rejects_unprovable_rasters(image):
    with pytest.raises(AmbiguousGridError, match="declare"):
        recover_nearest_neighbor_grid(image)


def test_recovery_rejects_inconsistent_axis_evidence():
    image = Image.new("RGB", (8, 8))
    image.putdata(
        [
            (17, 21, 21) if ((x // 2) + (y // 4)) % 2 == 0 else (229, 57, 53)
            for y in range(8)
            for x in range(8)
        ]
    )

    with pytest.raises(AmbiguousGridError, match="declare"):
        recover_nearest_neighbor_grid(image)


def test_recovery_uses_largest_byte_perfect_composite_scale():
    display = _checkerboard(4, 4).resize((16, 16), Image.Resampling.NEAREST)

    spec = recover_nearest_neighbor_grid(display)

    assert (spec.width, spec.height) == (4, 4)
    assert spec.scale == 4
    assert spec.area_factor == 16


def test_recovery_collapses_globally_repeated_three_by_three_semantic_pixels():
    logical = Image.new("RGB", (35, 34), "#111515")
    for y in range(4, 30):
        for x in range(7, 28):
            logical.putpixel((x, y), (229, 57, 53))
    display = logical.resize((105, 102), Image.Resampling.NEAREST)

    spec = recover_nearest_neighbor_grid(display)

    assert (spec.width, spec.height) == (35, 34)
    assert spec.scale == 3
    assert spec.area_factor == 9


def test_recovery_collapses_adjacent_duplicate_logical_rows_and_columns():
    base = _checkerboard(4, 4)
    duplicated = Image.new("RGB", (8, 8))
    source_columns = [index // 2 for index in range(8)]
    source_rows = [index // 2 for index in range(8)]
    for y, source_y in enumerate(source_rows):
        for x, source_x in enumerate(source_columns):
            duplicated.putpixel((x, y), base.getpixel((source_x, source_y)))
    display = duplicated.resize((32, 32), Image.Resampling.NEAREST)

    spec = recover_nearest_neighbor_grid(display)

    assert (spec.width, spec.height) == (4, 4)
    assert spec.scale == 8
