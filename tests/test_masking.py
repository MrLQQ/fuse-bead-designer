import pytest
from PIL import Image, ImageDraw

from fuse_bead_designer.masking import derive_subject_mask


def test_border_connected_white_is_empty_but_enclosed_warm_white_is_subject():
    image = Image.new("RGB", (7, 7), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((1, 1, 5, 5), fill="#111515")
    draw.point((3, 3), fill="#F7F4EA")

    mask = derive_subject_mask(image)

    assert mask.getpixel((0, 0)) == 0
    assert mask.getpixel((3, 3)) == 255


def test_rgb_background_mask_removes_only_border_connected_pixels():
    image = Image.new("RGB", (5, 5), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.rectangle((1, 1, 3, 3), fill="#111515")
    draw.point((2, 2), fill="#FFFFFF")

    mask = derive_subject_mask(image)

    assert mask.mode == "L"
    assert mask.getpixel((0, 2)) == 0
    assert mask.getpixel((1, 1)) == 255
    assert mask.getpixel((2, 2)) == 255


def test_rgba_mask_uses_alpha_occupancy_without_background_detection():
    image = Image.new("RGBA", (3, 2), (255, 255, 255, 0))
    image.putpixel((0, 0), (255, 255, 255, 255))
    image.putpixel((1, 0), (17, 21, 21, 1))

    mask = derive_subject_mask(image)

    assert list(mask.get_flattened_data()) == [255, 255, 0, 0, 0, 0]


@pytest.mark.parametrize("tolerance", [float("nan"), float("inf"), float("-inf"), True, "18"])
def test_mask_rejects_non_finite_or_non_numeric_tolerance(tolerance):
    image = Image.new("RGB", (1, 1), "white")

    with pytest.raises(ValueError, match="tolerance must be a finite non-negative number"):
        derive_subject_mask(image, tolerance=tolerance)
