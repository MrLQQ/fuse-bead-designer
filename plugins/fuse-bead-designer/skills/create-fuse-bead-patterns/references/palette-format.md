# Palette format / 配色格式

Provide a JSON array or CSV with these fields for every color:
`id`, `name`, `name_zh`, `hex`, `brand_code`. `brand_code` may be empty or
`null` for a generic palette. Use a real supplied code only; do not guess or
invent a brand name/code.

## Generic JSON example

```json
[
  {
    "id": "sky-blue",
    "name": "Sky Blue",
    "name_zh": "天蓝",
    "hex": "#65BCEB",
    "brand_code": null
  },
  {
    "id": "warm-white",
    "name": "Warm White",
    "name_zh": "暖白",
    "hex": "#F7F4EA",
    "brand_code": null
  }
]
```

## CSV example

```csv
id,name,name_zh,hex,brand_code
sky-blue,Sky Blue,天蓝,#65BCEB,
warm-white,Warm White,暖白,#F7F4EA,
```

Pass the file with `--palette <path>`. The compiler maps only to listed colors;
report nearest-color substitutions when the requested/inventory color is not an
exact match. White is a palette color, not an empty cell.
