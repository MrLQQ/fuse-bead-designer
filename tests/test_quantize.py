from PIL import Image
import pytest

from fuse_bead_designer.models import PaletteColor
from fuse_bead_designer.palettes import load_palette
from fuse_bead_designer.quantize import sample_cells


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
