"""Palette loading, validation, and perceptual nearest-color matching."""

import csv
from dataclasses import dataclass
import json
from pathlib import Path
import re

from .models import PaletteColor


_HEX_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
_GENERIC_PALETTE_PATH = Path(__file__).resolve().parents[2] / "assets" / "palettes" / "generic.json"
_CSV_COLUMNS = ("id", "name", "name_zh", "hex", "brand_code")


@dataclass(frozen=True)
class ColorMatch:
    color_id: str
    distance: float
    exact: bool


def load_palette(path: str | Path | None = None) -> list[PaletteColor]:
    """Load and validate the bundled JSON or user-provided JSON/CSV palette."""
    palette_path = _GENERIC_PALETTE_PATH if path is None else Path(path)
    suffix = palette_path.suffix.lower()
    if suffix == ".json":
        entries = _load_json_entries(palette_path)
    elif suffix == ".csv":
        entries = _load_csv_entries(palette_path)
    else:
        raise ValueError("palette path must end in .json or .csv")

    if not isinstance(entries, list):
        raise ValueError("palette must be a JSON array")
    if not entries:
        raise ValueError("palette must contain at least one color")
    palette = [_parse_palette_entry(entry) for entry in entries]
    _validate_unique_values(palette)
    return palette


def _load_json_entries(palette_path: Path) -> object:
    try:
        data = json.loads(palette_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("invalid palette JSON") from error
    return data


def _load_csv_entries(palette_path: Path) -> list[dict[str, str | None]]:
    try:
        with palette_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != list(_CSV_COLUMNS):
                raise ValueError("palette CSV header must be id,name,name_zh,hex,brand_code")
            entries = []
            for row in reader:
                if None in row or any(row.get(field) is None for field in _CSV_COLUMNS):
                    raise ValueError("palette CSV rows must have exactly five fields")
                entries.append({field: row[field] for field in _CSV_COLUMNS})
    except csv.Error as error:
        raise ValueError("invalid palette CSV") from error
    return entries


def nearest_color(rgb: tuple[int, int, int], palette: list[PaletteColor]) -> ColorMatch:
    """Return the palette color closest to *rgb* by CIE Lab Euclidean distance."""
    red, green, blue = _validate_rgb(rgb)
    if not palette:
        raise ValueError("palette must contain at least one color")

    input_rgb = (red, green, blue)
    input_lab = _srgb_to_lab(input_rgb)
    closest: PaletteColor | None = None
    closest_distance = float("inf")
    for color in palette:
        _validate_palette_color(color)
        candidate_distance = _lab_distance(input_lab, _srgb_to_lab(_hex_to_rgb(color.hex)))
        if candidate_distance < closest_distance:
            closest = color
            closest_distance = candidate_distance

    assert closest is not None
    return ColorMatch(
        color_id=closest.id,
        distance=closest_distance,
        exact=input_rgb == _hex_to_rgb(closest.hex),
    )


def _parse_palette_entry(entry: object) -> PaletteColor:
    if not isinstance(entry, dict):
        raise ValueError("palette entry must be an object")
    required = ("id", "name", "name_zh", "hex")
    for field_name in required:
        value = entry.get(field_name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"palette {field_name} must be a non-empty string")
    brand_code = entry.get("brand_code")
    if brand_code is not None and not isinstance(brand_code, str):
        raise ValueError("palette brand_code must be a string or null")
    color = PaletteColor(
        id=entry["id"],
        name=entry["name"],
        name_zh=entry["name_zh"],
        hex=entry["hex"],
        brand_code=brand_code,
    )
    _validate_palette_color(color)
    return color


def _validate_unique_values(palette: list[PaletteColor]) -> None:
    ids = [color.id for color in palette]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate palette id")
    brand_codes = [color.brand_code.strip() for color in palette if color.brand_code and color.brand_code.strip()]
    if len(brand_codes) != len(set(brand_codes)):
        raise ValueError("duplicate brand code")


def _validate_palette_color(color: PaletteColor) -> None:
    if not isinstance(color, PaletteColor):
        raise ValueError("palette entries must be PaletteColor instances")
    if not all(isinstance(value, str) and value for value in (color.id, color.name, color.name_zh)):
        raise ValueError("palette id and names must be non-empty strings")
    if not isinstance(color.hex, str) or not _HEX_PATTERN.fullmatch(color.hex):
        raise ValueError("invalid hex")
    if color.brand_code is not None and not isinstance(color.brand_code, str):
        raise ValueError("palette brand_code must be a string or null")


def _validate_rgb(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    if not isinstance(rgb, (tuple, list)) or len(rgb) != 3:
        raise ValueError("rgb must contain three integer channels")
    if any(not isinstance(channel, int) or isinstance(channel, bool) or not 0 <= channel <= 255 for channel in rgb):
        raise ValueError("rgb channels must be integers from 0 to 255")
    return tuple(rgb)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def _srgb_to_lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
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
