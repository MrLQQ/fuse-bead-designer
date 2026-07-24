"""Portable PNG rendering for validated fuse-bead patterns."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import CompileReport, PaletteColor, Pattern


FONT_PATH = Path(__file__).resolve().parents[2] / "assets" / "fonts" / "NotoSansCJKsc-Regular.otf"
GRID_LEFT = 54
GRID_TOP = 66
LEGEND_GAP = 38
LEGEND_WIDTH = 390
RIGHT_PADDING = 28
BOTTOM_PADDING = 34
LEGEND_ROW_HEIGHT = 64
LEGEND_ROWS_TOP = 108
CELL_GRID = (184, 184, 184)
FIVE_CELL_GRID = (82, 82, 82)
BOARD_GRID = (30, 30, 30)
TEXT_PRIMARY = (32, 36, 37)
TEXT_SECONDARY = (82, 90, 93)
DIVIDER = (170, 176, 178)


def render_template(pattern: Pattern, *, cell_size: int = 18) -> Image.Image:
    """Render a printable template using ``Pattern.cells`` as the only cell source."""
    pattern.validate()
    _validate_cell_size(cell_size)
    title_font = _load_font(20)
    legend_title_font = _load_font(24)
    name_font = _load_font(16)
    metadata_font = _load_font(13)
    count_font = _load_font(20)
    label_font = _load_font(max(9, min(11, cell_size - 3)))
    grid_width = pattern.width * cell_size
    grid_height = pattern.height * cell_size
    legend_left = GRID_LEFT + grid_width + LEGEND_GAP
    used_rows = _used_palette_rows(pattern)
    summary_top = LEGEND_ROWS_TOP + len(used_rows) * LEGEND_ROW_HEIGHT + 12
    legend_bottom = summary_top + 86
    image = Image.new(
        "RGBA",
        (
            legend_left + LEGEND_WIDTH + RIGHT_PADDING,
            max(GRID_TOP + grid_height + BOTTOM_PADDING, legend_bottom + BOTTOM_PADDING),
        ),
        "white",
    )
    draw = ImageDraw.Draw(image)
    colors = {color.id: color for color in pattern.palette}

    draw.text(
        (GRID_LEFT, 14),
        f"Fuse-bead template · {pattern.width} × {pattern.height}",
        fill=TEXT_PRIMARY,
        font=title_font,
        stroke_width=1,
        stroke_fill=TEXT_PRIMARY,
    )
    for row, cells in enumerate(pattern.cells):
        for column, color_id in enumerate(cells):
            left = GRID_LEFT + column * cell_size
            top = GRID_TOP + row * cell_size
            fill = "#FFFFFF" if color_id is None else colors[color_id].hex
            draw.rectangle((left, top, left + cell_size, top + cell_size), fill=fill)

    _draw_labels(draw, pattern, cell_size, label_font)
    _draw_grid(draw, pattern, cell_size)
    _draw_legend(
        draw,
        pattern,
        used_rows,
        legend_left,
        legend_title_font,
        name_font,
        metadata_font,
        count_font,
    )
    return image


def render_review(pattern: Pattern, report: CompileReport | None = None, *, cell_size: int = 18) -> Image.Image:
    """Render review markers for inferred cells and conservative cleanup changes."""
    image = render_template(pattern, cell_size=cell_size)
    draw = ImageDraw.Draw(image)
    _draw_review_markers(draw, pattern.inferred_cells, cell_size, "#F28C28")
    if report is not None:
        _draw_review_markers(draw, report.cleanup_changes, cell_size, "#00A6D6")
    return image


def _draw_grid(draw: ImageDraw.ImageDraw, pattern: Pattern, cell_size: int) -> None:
    right = GRID_LEFT + pattern.width * cell_size
    bottom = GRID_TOP + pattern.height * cell_size
    for column in range(pattern.width + 1):
        x = GRID_LEFT + column * cell_size
        color = FIVE_CELL_GRID if column % 5 == 0 else CELL_GRID
        draw.line((x, GRID_TOP, x, bottom), fill=color, width=1)
    for row in range(pattern.height + 1):
        y = GRID_TOP + row * cell_size
        color = FIVE_CELL_GRID if row % 5 == 0 else CELL_GRID
        draw.line((GRID_LEFT, y, right, y), fill=color, width=1)
    for column in range(0, pattern.width + 1, pattern.module_size):
        x = GRID_LEFT + column * cell_size
        draw.line((x, GRID_TOP, x, bottom), fill=BOARD_GRID, width=2)
    for row in range(0, pattern.height + 1, pattern.module_size):
        y = GRID_TOP + row * cell_size
        draw.line((GRID_LEFT, y, right, y), fill=BOARD_GRID, width=2)


def _draw_labels(
    draw: ImageDraw.ImageDraw,
    pattern: Pattern,
    cell_size: int,
    font: ImageFont.FreeTypeFont,
) -> None:
    for milestone in _coordinate_labels(pattern.width):
        label = str(milestone)
        box = draw.textbbox((0, 0), label, font=font)
        x = GRID_LEFT + (milestone - 0.5) * cell_size - (box[2] - box[0]) / 2
        draw.text((x, GRID_TOP - 19), label, fill=TEXT_SECONDARY, font=font)
    for milestone in _coordinate_labels(pattern.height):
        label = str(milestone)
        box = draw.textbbox((0, 0), label, font=font)
        y = (
            GRID_TOP
            + (milestone - 0.5) * cell_size
            - (box[3] - box[1]) / 2
            - box[1]
        )
        draw.text(
            (GRID_LEFT - (box[2] - box[0]) - 10, y),
            label,
            fill=TEXT_SECONDARY,
            font=font,
        )


def _draw_legend(
    draw: ImageDraw.ImageDraw,
    pattern: Pattern,
    rows: list[tuple[PaletteColor, int]],
    legend_left: int,
    title_font: ImageFont.FreeTypeFont,
    name_font: ImageFont.FreeTypeFont,
    metadata_font: ImageFont.FreeTypeFont,
    count_font: ImageFont.FreeTypeFont,
) -> None:
    board_count = pattern.board_columns * pattern.board_rows
    legend_right = legend_left + LEGEND_WIDTH - 12
    draw.text(
        (legend_left, 14),
        "Color key / 用量",
        fill=TEXT_PRIMARY,
        font=title_font,
        stroke_width=1,
        stroke_fill=TEXT_PRIMARY,
    )
    draw.text(
        (legend_left, 49),
        "Colored cells only; white grid cells are empty.",
        fill=TEXT_SECONDARY,
        font=metadata_font,
    )
    draw.text(
        (legend_left, 72),
        "有色格计入拼豆；纯白空格不计。",
        fill=TEXT_SECONDARY,
        font=metadata_font,
    )
    for index, (color, count) in enumerate(rows):
        top = LEGEND_ROWS_TOP + index * LEGEND_ROW_HEIGHT
        draw.rectangle(
            (legend_left, top, legend_left + 38, top + 38),
            fill=color.hex,
            outline=(105, 113, 116),
            width=1,
        )
        draw.text(
            (legend_left + 54, top - 2),
            f"{color.name} / {color.name_zh}",
            fill=TEXT_PRIMARY,
            font=name_font,
            stroke_width=1,
            stroke_fill=TEXT_PRIMARY,
        )
        draw.text(
            (legend_left + 54, top + 22),
            _color_metadata(color),
            fill=TEXT_SECONDARY,
            font=metadata_font,
        )
        count_box = draw.textbbox((0, 0), str(count), font=count_font)
        draw.text(
            (legend_right - (count_box[2] - count_box[0]), top + 7),
            str(count),
            fill=TEXT_PRIMARY,
            font=count_font,
            stroke_width=1,
            stroke_fill=TEXT_PRIMARY,
        )
    total_top = LEGEND_ROWS_TOP + len(rows) * LEGEND_ROW_HEIGHT + 12
    draw.line((legend_left, total_top, legend_right, total_top), fill=DIVIDER, width=1)
    draw.text(
        (legend_left, total_top + 20),
        "Total beads / 总计",
        fill=TEXT_PRIMARY,
        font=name_font,
        stroke_width=1,
        stroke_fill=TEXT_PRIMARY,
    )
    total = str(pattern.total_beads)
    total_box = draw.textbbox((0, 0), total, font=count_font)
    draw.text(
        (legend_right - (total_box[2] - total_box[0]), total_top + 17),
        total,
        fill=TEXT_PRIMARY,
        font=count_font,
        stroke_width=1,
        stroke_fill=TEXT_PRIMARY,
    )
    draw.text(
        (legend_left, total_top + 55),
        f"Boards / 拼豆板：{board_count}  ({pattern.board_columns} × {pattern.board_rows})",
        fill=TEXT_SECONDARY,
        font=metadata_font,
    )


def _coordinate_labels(size: int) -> list[int]:
    """Return sparse coordinate labels for five-cell navigation."""
    milestones = list(range(5, size + 1, 5))
    if size >= 5 and size % 5:
        milestones.append(size)
    return milestones


def _used_palette_rows(pattern: Pattern) -> list[tuple[PaletteColor, int]]:
    """Return used colors in palette order with their canonical counts."""
    counts = pattern.color_counts()
    return [
        (color, counts[color.id])
        for color in pattern.palette
        if counts.get(color.id, 0) > 0
    ]


def _color_metadata(color: PaletteColor) -> str:
    """Format a color's HEX and optional brand code without duplication."""
    if color.brand_code:
        return f"{color.hex} · {color.brand_code}"
    return color.hex


def _draw_review_markers(
    draw: ImageDraw.ImageDraw,
    coordinates: list[tuple[int, int]],
    cell_size: int,
    color: str,
) -> None:
    for column, row in coordinates:
        left = GRID_LEFT + column * cell_size
        top = GRID_TOP + row * cell_size
        draw.rectangle((left + 1, top + 1, left + cell_size - 1, top + cell_size - 1), outline=color, width=2)


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"bundled CJK font is missing: {FONT_PATH}")
    return ImageFont.truetype(FONT_PATH, size)


def _validate_cell_size(cell_size: int) -> None:
    if not isinstance(cell_size, int) or isinstance(cell_size, bool) or cell_size < 4:
        raise ValueError("cell_size must be an integer of at least 4")
