import json

import pytest

from fuse_bead_designer.models import PaletteColor
from fuse_bead_designer.palettes import load_palette, nearest_color


def test_generic_palette_is_the_exact_initial_bilingual_16_color_set():
    palette = load_palette()

    assert [(color.id, color.name, color.name_zh, color.hex, color.brand_code) for color in palette] == [
        ("black", "Black", "黑色", "#111515", None),
        ("charcoal", "Charcoal", "炭黑", "#273033", None),
        ("gray", "Gray", "灰色", "#596564", None),
        ("warm-white", "Warm White", "暖白", "#F7F4EA", None),
        ("red", "Red", "红色", "#E53935", None),
        ("orange", "Orange", "橙色", "#FB8C00", None),
        ("yellow", "Yellow", "黄色", "#FFE000", None),
        ("lime", "Lime", "荧光绿", "#69E51C", None),
        ("green", "Green", "绿色", "#00B66A", None),
        ("dark-green", "Dark Green", "深绿", "#087A52", None),
        ("turquoise", "Turquoise", "青绿", "#00CFC1", None),
        ("blue", "Blue", "蓝色", "#2684FF", None),
        ("purple", "Purple", "紫色", "#8E44AD", None),
        ("pink", "Pink", "粉色", "#FF6FAE", None),
        ("brown", "Brown", "棕色", "#76503A", None),
        ("tan", "Tan", "浅棕", "#C49A6C", None),
    ]


def test_custom_palette_rejects_duplicate_brand_codes(tmp_path):
    path = tmp_path / "palette.json"
    path.write_text(json.dumps([
        {"id": "a", "name": "A", "name_zh": "甲", "hex": "#000000", "brand_code": "01"},
        {"id": "b", "name": "B", "name_zh": "乙", "hex": "#FFFFFF", "brand_code": "01"},
    ]), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate brand code"):
        load_palette(path)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("{", "invalid palette JSON"),
        (json.dumps({"id": "red"}), "palette must be a JSON array"),
        (json.dumps(["red"]), "palette entry must be an object"),
        (json.dumps([{"id": "red", "name": "Red", "name_zh": "红色", "hex": "#12345G"}]), "invalid hex"),
        (json.dumps([
            {"id": "red", "name": "Red", "name_zh": "红色", "hex": "#FF0000"},
            {"id": "red", "name": "Red 2", "name_zh": "红二", "hex": "#00FF00"},
        ]), "duplicate palette id"),
    ],
)
def test_custom_palette_rejects_invalid_json_shapes_hex_and_ids(tmp_path, payload, message):
    path = tmp_path / "palette.json"
    path.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_palette(path)


def test_custom_palette_allows_repeated_empty_brand_codes(tmp_path):
    path = tmp_path / "palette.json"
    path.write_text(json.dumps([
        {"id": "a", "name": "A", "name_zh": "甲", "hex": "#000000", "brand_code": ""},
        {"id": "b", "name": "B", "name_zh": "乙", "hex": "#FFFFFF", "brand_code": "   "},
    ]), encoding="utf-8")

    assert [color.brand_code for color in load_palette(path)] == ["", "   "]


def test_custom_csv_palette_accepts_utf8_bom_and_preserves_brand_codes(tmp_path):
    path = tmp_path / "palette.csv"
    path.write_text(
        "id,name,name_zh,hex,brand_code\nblack,Black,黑色,#111515,A-01\n",
        encoding="utf-8-sig",
    )

    assert load_palette(path) == [
        PaletteColor("black", "Black", "黑色", "#111515", "A-01")
    ]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("id,name,hex,brand_code\na,Alpha,#000000,01\n", "palette CSV header"),
        (
            "id,name,name_zh,hex,brand_code,extra\na,Alpha,甲,#000000,01,unexpected\n",
            "palette CSV header",
        ),
        (
            "id,name,name_zh,hex,brand_code\na,Alpha,甲,#000000,01,unexpected\n",
            "palette CSV rows must have exactly five fields",
        ),
    ],
)
def test_custom_csv_palette_rejects_malformed_columns(tmp_path, payload, message):
    path = tmp_path / "palette.csv"
    path.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_palette(path)


def test_nearest_color_returns_deterministic_exact_match():
    palette = [
        PaletteColor("red", "Red", "红色", "#E53935"),
        PaletteColor("blue", "Blue", "蓝色", "#2684FF"),
    ]

    match = nearest_color((229, 57, 53), palette)

    assert match.color_id == "red"
    assert match.distance == 0.0
    assert match.exact is True
