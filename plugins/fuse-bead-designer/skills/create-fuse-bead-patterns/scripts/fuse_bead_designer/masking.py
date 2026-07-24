"""Subject occupancy masks with explicit white-bead preservation."""

from collections import deque
from statistics import median

from PIL import Image


def derive_subject_mask(image: Image.Image, tolerance: float = 18) -> Image.Image:
    """Return an ``L`` mask where occupied subject pixels are 255.

    Alpha, when present, is authoritative: any non-zero alpha value is
    occupied.  Opaque images instead remove only pixels connected to the
    image border that are perceptually close to the median corner color.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a Pillow Image")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
        raise ValueError("tolerance must be a non-negative number")
    if tolerance < 0:
        raise ValueError("tolerance must be a non-negative number")

    if "A" in image.getbands() or "transparency" in image.info:
        return _alpha_occupancy_mask(image)
    return _opaque_subject_mask(image.convert("RGB"), float(tolerance))


def _alpha_occupancy_mask(image: Image.Image) -> Image.Image:
    alpha = image.convert("RGBA").getchannel("A")
    return alpha.point(lambda value: 255 if value > 0 else 0, mode="L")


def _opaque_subject_mask(image: Image.Image, tolerance: float) -> Image.Image:
    width, height = image.size
    if width == 0 or height == 0:
        return Image.new("L", image.size)

    pixels = image.load()
    corners = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    background_lab = _srgb_to_lab(tuple(median(channel) for channel in zip(*corners)))
    near_background: dict[tuple[int, int, int], bool] = {}

    def is_near_background(pixel: tuple[int, int, int]) -> bool:
        if pixel not in near_background:
            near_background[pixel] = _lab_distance(_srgb_to_lab(pixel), background_lab) <= tolerance
        return near_background[pixel]

    background = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        queue.extend(((x, 0), (x, height - 1)))
    for y in range(1, height - 1):
        queue.extend(((0, y), (width - 1, y)))

    while queue:
        x, y = queue.popleft()
        index = y * width + x
        if background[index] or not is_near_background(pixels[x, y]):
            continue
        background[index] = 1
        if x > 0:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y > 0:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))

    return Image.frombytes("L", image.size, bytes(255 if value == 0 else 0 for value in background))


def _srgb_to_lab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    red, green, blue = (_linear_channel(channel / 255.0) for channel in rgb)
    x = (0.4124564 * red + 0.3575761 * green + 0.1804375 * blue) / 0.95047
    y = 0.2126729 * red + 0.7151522 * green + 0.0721750 * blue
    z = (0.0193339 * red + 0.1191920 * green + 0.9503041 * blue) / 1.08883
    fx, fy, fz = (_lab_axis(value) for value in (x, y, z))
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def _linear_channel(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _lab_axis(value: float) -> float:
    return value ** (1 / 3) if value > 0.008856 else 7.787 * value + 16 / 116


def _lab_distance(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(first, second)) ** 0.5
