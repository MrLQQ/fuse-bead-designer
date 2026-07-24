import csv
import json

from PIL import ImageFont

from fuse_bead_designer.io import write_artifacts
from fuse_bead_designer.models import (
    CompileReport,
    PaletteColor,
    Pattern,
    VerificationState,
)
from fuse_bead_designer.render import FONT_PATH, render_template


def make_pattern(*, inferred_cells=None, is_custom_size=True):
    return Pattern(
        width=3,
        height=2,
        module_size=29,
        palette=[
            PaletteColor("red", "Red", "红色", "#FF0000", "R01"),
            PaletteColor("white", "White", "白色", "#F7F4EA"),
        ],
        cells=[["red", None, "white"], ["red", "red", None]],
        verification=VerificationState.VERIFIED,
        is_custom_size=is_custom_size,
        inferred_cells=inferred_cells or [],
    )


def test_written_artifacts_share_exact_counts_and_utf8_chinese(tmp_path):
    pattern = make_pattern()

    write_artifacts(pattern, tmp_path)

    data = json.loads((tmp_path / "pattern.json").read_text(encoding="utf-8"))
    raw_json = (tmp_path / "pattern.json").read_text(encoding="utf-8")
    with (tmp_path / "colors.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))

    assert data["total_beads"] == sum(int(row["count"]) for row in rows) == 4
    assert "红色" in raw_json
    assert (tmp_path / "template.png").exists()
    assert not (tmp_path / "review.png").exists()


def test_colors_csv_uses_canonical_column_order_and_palette_metadata(tmp_path):
    write_artifacts(make_pattern(), tmp_path)

    with (tmp_path / "colors.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        rows = list(reader)

    assert header == ["id", "name", "name_zh", "hex", "brand_code", "count"]
    assert rows == [
        ["red", "Red", "红色", "#FF0000", "R01", "3"],
        ["white", "White", "白色", "#F7F4EA", "", "1"],
    ]


def test_report_contains_full_compile_fields(tmp_path):
    report = CompileReport(
        classification="pixel-art",
        removed_interference=["watermark"],
        board_decision={"columns": 1, "rows": 1},
        palette_decision={"source": "generic"},
        cleanup_changes=[(1, 1)],
        warnings=["check outline"],
        verification=VerificationState.REVIEW_REQUIRED,
    )

    write_artifacts(make_pattern(), tmp_path, report=report)

    written = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert written == {
        "classification": "pixel-art",
        "removed_interference": ["watermark"],
        "board_decision": {"columns": 1, "rows": 1},
        "palette_decision": {"source": "generic"},
        "cleanup_changes": [[1, 1]],
        "warnings": ["check outline"],
        "verification": "review-required",
    }


def test_review_overlay_is_only_written_for_inferred_or_cleanup_markers(tmp_path):
    write_artifacts(make_pattern(inferred_cells=[(0, 0)]), tmp_path / "inferred")
    assert (tmp_path / "inferred" / "review.png").exists()

    cleanup_report = CompileReport(
        classification="pixel-art",
        removed_interference=[],
        board_decision={},
        palette_decision={},
        cleanup_changes=[(1, 1)],
        warnings=[],
        verification=VerificationState.VERIFIED,
    )
    write_artifacts(make_pattern(), tmp_path / "cleanup", report=cleanup_report)
    assert (tmp_path / "cleanup" / "review.png").exists()

    write_artifacts(make_pattern(), tmp_path / "none")
    assert not (tmp_path / "none" / "review.png").exists()


def test_template_contains_grid_labels_legend_and_portable_cjk_font():
    pattern = make_pattern()
    image = render_template(pattern, cell_size=18)

    assert image.width > pattern.width * 18
    assert image.height > pattern.height * 18
    assert image.getbbox() is not None
    assert FONT_PATH.exists()
    assert ImageFont.truetype(FONT_PATH, 16).getmask("红色").getbbox() is not None


def test_standard_template_draws_five_cell_and_29_board_boundaries():
    pattern = Pattern(
        width=29,
        height=29,
        module_size=29,
        palette=[],
        cells=[[None] * 29 for _ in range(29)],
        verification=VerificationState.VERIFIED,
    )

    image = render_template(pattern, cell_size=4)

    # Grid origin is public renderer geometry: labels occupy the 32-pixel margin.
    grid_left, grid_top = 32, 32
    assert image.getpixel((grid_left + 5 * 4, grid_top + 2))[:3] == (82, 82, 82)
    assert image.getpixel((grid_left + 29 * 4, grid_top + 2))[:3] == (30, 30, 30)
