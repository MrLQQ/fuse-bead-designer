"""Portable PNG rendering for validated fuse-bead patterns."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import CompileReport, Pattern


FONT_PATH = Path(__file__).resolve().parents[2] / "assets" / "fonts" / "NotoSansCJKsc-Regular.otf"
GRID_LEFT = 32
GRID_TOP = 32
LEGEND_GAP = 28
LEGEND_WIDTH = 270
CELL_GRID = (184, 184, 184)
FIVE_CELL_GRID = (82, 82, 82)
BOARD_GRID = (30, 30, 30)


def render_template(pattern: Pattern, *, cell_size: int = 18) -> Image.Image:
    """Render a printable template using ``Pattern.cells`` as the only cell source."""
    pattern.validate()
    _validate_cell_size(cell_size)
    font = _load_font(max(10, cell_size - 4))
    label_font = _load_font(max(9, cell_size - 6))
    grid_width = pattern.width * cell_size
    grid_height = pattern.height * cell_size
    legend_left = GRID_LEFT + grid_width + LEGEND_GAP
    legend_height = 56 + max(1, len(pattern.palette)) * max(26, cell_size + 8)
    image = Image.new(
        "RGBA",
        (
            legend_left + LEGEND_WIDTH + GRID_LEFT,
            max(GRID_TOP + grid_height + GRID_TOP, GRID_TOP + legend_height + GRID_TOP),
        ),
        "white",
    )
    draw = ImageDraw.Draw(image)
    colors = {color.id: color for color in pattern.palette}

    for row, cells in enumerate(pattern.cells):
        for column, color_id in enumerate(cells):
            left = GRID_LEFT + column * cell_size
            top = GRID_TOP + row * cell_size
            fill = "#FFFFFF" if color_id is None else colors[color_id].hex
            draw.rectangle((left, top, left + cell_size, top + cell_size), fill=fill)

    _draw_labels(draw, pattern, cell_size, label_font)
    _draw_grid(draw, pattern, cell_size)
    _draw_legend(draw, pattern, legend_left, font, label_font)
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
    if not pattern.is_custom_size:
        for column in range(0, pattern.width + 1, 29):
            x = GRID_LEFT + column * cell_size
            draw.line((x, GRID_TOP, x, bottom), fill=BOARD_GRID, width=2)
        for row in range(0, pattern.height + 1, 29):
            y = GRID_TOP + row * cell_size
            draw.line((GRID_LEFT, y, right, y), fill=BOARD_GRID, width=2)


def _draw_labels(
    draw: ImageDraw.ImageDraw,
    pattern: Pattern,
    cell_size: int,
    font: ImageFont.FreeTypeFont,
) -> None:
    for column in range(pattern.width):
        label = str(column + 1)
        box = draw.textbbox((0, 0), label, font=font)
        x = GRID_LEFT + column * cell_size + (cell_size - (box[2] - box[0])) // 2
        draw.text((x, GRID_TOP - cell_size - 2), label, fill="black", font=font)
    for row in range(pattern.height):
        label = str(row + 1)
        box = draw.textbbox((0, 0), label, font=font)
        y = GRID_TOP + row * cell_size + (cell_size - (box[3] - box[1])) // 2 - box[1]
        draw.text((GRID_LEFT - (box[2] - box[0]) - 6, y), label, fill="black", font=font)


def _draw_legend(
    draw: ImageDraw.ImageDraw,
    pattern: Pattern,
    legend_left: int,
    font: ImageFont.FreeTypeFont,
    small_font: ImageFont.FreeTypeFont,
) -> None:
    counts = pattern.color_counts()
    board_count = pattern.board_columns * pattern.board_rows
    draw.text((legend_left, GRID_TOP), "颜色 / Colors", fill="black", font=font)
    line_height = max(26, font.size + 10)
    for index, color in enumerate(pattern.palette):
        top = GRID_TOP + 30 + index * line_height
        draw.rectangle((legend_left, top, legend_left + 18, top + 18), fill=color.hex, outline="black")
        draw.text((legend_left + 26, top - 3), f"{color.name} / {color.name_zh}", fill="black", font=font)
        code = color.brand_code or color.hex
        draw.text(
            (legend_left + 26, top + max(12, small_font.size - 1)),
            f"{color.hex} / {code} · {counts.get(color.id, 0)}",
            fill="black",
            font=small_font,
        )
    total_top = GRID_TOP + 38 + max(1, len(pattern.palette)) * line_height
    draw.text((legend_left, total_top), f"总珠数 / Total: {pattern.total_beads}", fill="black", font=font)
    draw.text((legend_left, total_top + line_height), f"拼豆板 / Boards: {board_count}", fill="black", font=font)


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
