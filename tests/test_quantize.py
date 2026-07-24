from PIL import Image
import pytest

from fuse_bead_designer.models import PaletteColor
from fuse_bead_designer.palettes import load_palette
from fuse_bead_designer.quantize import sample_cell_centers, sample_cells


def two_color_subject():
    image = Image.new("RGB", (4, 2), "#111515")
    for x in range(2, 4):
        for y in range(2):
            image.putpixel((x, y), rgb("E53935"))
    return image, Image.new("L", image.size, 255)


def palette_color(color_id, value):
    return PaletteColor(color_id, color_id, color_id, value)


def rgb(value):
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def test_quantization_is_deterministic_and_has_no_dithering():
    image, mask = two_color_subject()

    first = sample_cells(image, mask, 2, 1, load_palette())
    second = sample_cells(image, mask, 2, 1, load_palette())

    assert first == second
    assert {cell.color_id for row in first for cell in row if cell.occupied} <= {
        color.id for color in load_palette()
    }
    assert [cell.color_id for cell in first[0]] == ["black", "red"]


def test_exactly_half_mask_coverage_is_occupied_and_samples_only_occupied_pixels():
    image = Image.new("RGB", (2, 2), "#FFFFFF")
    image.putpixel((0, 0), rgb("111515"))
    image.putpixel((1, 0), rgb("111515"))
    mask = Image.new("L", image.size, 0)
    mask.putpixel((0, 0), 255)
    mask.putpixel((1, 0), 255)

    cells = sample_cells(image, mask, 1, 1, load_palette())

    assert cells[0][0].occupied is True
    assert cells[0][0].color_id == "black"


def test_source_rectangles_cover_non_divisible_dimensions_without_dropping_pixels():
    image = Image.new("RGB", (5, 1), "#111515")
    image.putpixel((3, 0), rgb("E53935"))
    image.putpixel((4, 0), rgb("E53935"))
    mask = Image.new("L", image.size, 255)

    cells = sample_cells(image, mask, 2, 1, load_palette())

    assert [cell.color_id for cell in cells[0]] == ["black", "red"]
    assert cells[0][1].source_rgb == (229.0, 57.0, 53.0)


def test_empty_mask_and_empty_source_cell_are_unoccupied():
    image = Image.new("RGB", (1, 1), "#111515")

    assert sample_cells(image, Image.new("L", image.size, 0), 1, 1, load_palette())[0][0].occupied is False
    cells = sample_cells(image, Image.new("L", image.size, 255), 2, 1, load_palette())
    assert sorted(cell.occupied for cell in cells[0]) == [False, True]


def test_color_limit_validates_and_uses_palette_id_ties_then_nearest_remap():
    image = Image.new("RGB", (3, 1))
    image.putdata([rgb("000000"), rgb("808080"), rgb("FFFFFF")])
    mask = Image.new("L", image.size, 255)
    palette = [
        palette_color("zblack", "#000000"),
        palette_color("agrey", "#808080"),
        palette_color("mwhite", "#FFFFFF"),
    ]

    cells = sample_cells(image, mask, 3, 1, palette, color_limit=2)

    assert [cell.color_id for cell in cells[0]] == ["agrey", "agrey", "mwhite"]
    with pytest.raises(ValueError, match="color_limit must be a positive integer"):
        sample_cells(image, mask, 1, 1, palette, color_limit=0)
    with pytest.raises(ValueError, match="color_limit must be a positive integer"):
        sample_cells(image, mask, 1, 1, palette, color_limit=True)


def test_default_color_limit_is_sixteen_for_a_larger_custom_palette():
    colors = [f"#{value:02X}{value:02X}{value:02X}" for value in range(0, 256, 13)][:20]
    image = Image.new("RGB", (20, 1))
    image.putdata([rgb(color[1:]) for color in colors])
    palette = [palette_color(f"c{index:02d}", color) for index, color in enumerate(colors)]

    cells = sample_cells(image, Image.new("L", image.size, 255), 20, 1, palette)

    assert len({cell.color_id for cell in cells[0] if cell.occupied}) == 16


def test_center_sampling_preserves_declared_grid_empty_cells_and_highlight():
    cell_size = 12
    padding = 5
    width, height = 4, 3
    grid_box = (
        padding,
        padding,
        padding + width * cell_size,
        padding + height * cell_size,
    )
    image = Image.new("RGB", (grid_box[2] + padding, grid_box[3] + padding), "#FFFFFF")
    mask = Image.new("L", image.size, 255)

    for row in range(height):
        for column in range(width):
            left = padding + column * cell_size
            top = padding + row * cell_size
            color = "#111515"
            if (column, row) == (2, 1):
                color = "#E53935"
            for y in range(top, top + cell_size):
                for x in range(left, left + cell_size):
                    image.putpixel((x, y), rgb(color[1:]))

    empty_cell = (0, 2)
    empty_left = padding + empty_cell[0] * cell_size
    empty_top = padding + empty_cell[1] * cell_size
    for y in range(empty_top, empty_top + cell_size):
        for x in range(empty_left, empty_left + cell_size):
            mask.putpixel((x, y), 0)

    cells = sample_cell_centers(
        image,
        mask,
        width,
        height,
        load_palette(),
        grid_box=grid_box,
    )

    assert (len(cells[0]), len(cells)) == (width, height)
    assert cells[empty_cell[1]][empty_cell[0]].occupied is False
    assert cells[1][2].color_id == "red"
    assert sum(cell.occupied for row in cells for cell in row) == width * height - 1
    assert sum(cell.color_id == "red" for row in cells for cell in row) == 1


def test_center_sampling_uses_small_odd_window_instead_of_rectangle_median():
    image = Image.new("RGB", (12, 12), "#111515")
    for y in range(4, 7):
        for x in range(4, 7):
            image.putpixel((x, y), rgb("E53935"))

    cells = sample_cell_centers(
        image,
        Image.new("L", image.size, 255),
        1,
        1,
        load_palette(),
    )

    assert cells[0][0].color_id == "red"
    assert cells[0][0].source_rgb == (229.0, 57.0, 53.0)


def test_center_sampling_requires_explicit_grid_box_to_exclude_padding():
    image = Image.new("RGB", (18, 8), "#FFFFFF")
    mask = Image.new("L", image.size, 255)
    for y in range(8):
        for x in range(10, 18):
            image.putpixel((x, y), rgb("111515"))

    unboxed = sample_cell_centers(image, mask, 1, 1, load_palette())
    boxed = sample_cell_centers(
        image,
        mask,
        1,
        1,
        load_palette(),
        grid_box=(10, 0, 18, 8),
    )

    assert unboxed[0][0].color_id == "warm-white"
    assert boxed[0][0].color_id == "black"


def test_center_sampling_reuses_color_limit_validation_and_remapping():
    image = Image.new("RGB", (12, 4))
    for column, color in enumerate(("000000", "808080", "FFFFFF")):
        for y in range(4):
            for x in range(column * 4, (column + 1) * 4):
                image.putpixel((x, y), rgb(color))
    palette = [
        palette_color("zblack", "#000000"),
        palette_color("agrey", "#808080"),
        palette_color("mwhite", "#FFFFFF"),
    ]

    cells = sample_cell_centers(
        image,
        Image.new("L", image.size, 255),
        3,
        1,
        palette,
        color_limit=2,
    )

    assert [cell.color_id for cell in cells[0]] == ["agrey", "agrey", "mwhite"]
    with pytest.raises(ValueError, match="color_limit must be a positive integer"):
        sample_cell_centers(image, Image.new("L", image.size, 255), 1, 1, palette, color_limit=0)


@pytest.mark.parametrize(
    "grid_box",
    [
        (-1, 0, 2, 2),
        (0, 0, 3, 2),
        (1, 0, 1, 2),
        (0, 0, 2, True),
    ],
)
def test_center_sampling_rejects_invalid_grid_box(grid_box):
    image = Image.new("RGB", (2, 2), "#111515")

    with pytest.raises(ValueError, match="grid_box"):
        sample_cell_centers(
            image,
            Image.new("L", image.size, 255),
            1,
            1,
            load_palette(),
            grid_box=grid_box,
        )
