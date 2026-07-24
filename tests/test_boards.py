import math
import sys

import pytest

from fuse_bead_designer.boards import (
    STANDARD_CANDIDATES,
    BoardLayout,
    layout_boards,
    select_board,
)
from fuse_bead_designer.models import Pattern, VerificationState
from fuse_bead_designer.render import BOARD_GRID, GRID_LEFT, GRID_TOP, render_template


REQUIRED_STANDARD_CANDIDATES = (
    (29, 29),
    (58, 29),
    (29, 58),
    (58, 58),
    (87, 58),
    (58, 87),
)


def _independent_score(candidate, source_aspect, detail_score):
    width, height = candidate
    board_count = (width // 29) * (height // 29)
    return (
        abs(math.log((width / height) / source_aspect))
        + max(0.0, detail_score - min(width, height) / 58)
        + 0.08 * max(0, board_count - 1)
    )


def test_wide_subject_prefers_two_horizontal_boards():
    selected = select_board(subject_width=1600, subject_height=800)

    assert (selected.width, selected.height) == (58, 29)
    assert selected.requires_confirmation is False


def test_square_subject_defaults_to_one_board_when_detail_is_low():
    selected = select_board(1000, 1000, detail_score=0.2)

    assert (selected.width, selected.height) == (29, 29)


def test_explicit_custom_size_wins():
    selected = select_board(1000, 1000, explicit_size=(40, 36))

    assert (selected.width, selected.height) == (40, 36)
    assert selected.is_custom is True
    assert (selected.board_columns, selected.board_rows) == (2, 2)
    assert selected.board_count == 4
    assert selected.alternatives == ()


def test_more_than_four_boards_requires_confirmation():
    selected = select_board(1800, 1200, detail_score=1.0, max_boards=6)

    assert selected.board_count > 4
    assert selected.requires_confirmation is True


def test_standard_candidates_match_the_required_literal_dimensions():
    assert STANDARD_CANDIDATES == REQUIRED_STANDARD_CANDIDATES


def test_balanced_subject_exposes_close_alternatives_by_independent_score():
    source_aspect = 1500 / 1000
    detail_score = 0.2
    selected = select_board(1500, 1000, detail_score=detail_score)
    selected_score = _independent_score(
        (selected.width, selected.height), source_aspect, detail_score
    )

    assert selected.alternatives
    assert (selected.width, selected.height) not in selected.alternatives
    assert selected.score == pytest.approx(selected_score)
    assert all(candidate in REQUIRED_STANDARD_CANDIDATES for candidate in selected.alternatives)
    assert all(
        abs(_independent_score(candidate, source_aspect, detail_score) - selected_score)
        <= 0.05
        for candidate in selected.alternatives
    )


def test_standard_selection_is_a_standard_candidate_with_matching_board_count():
    selected = select_board(1600, 800)

    assert (selected.width, selected.height) in STANDARD_CANDIDATES
    assert selected.board_count == selected.board_columns * selected.board_rows


def test_selected_score_uses_aspect_detail_and_board_penalties():
    selected = select_board(1600, 800, detail_score=0.7)

    expected = (
        abs(math.log((58 / 29) / 2))
        + max(0.0, 0.7 - 29 / 58)
        + 0.08 * (2 - 1)
    )
    assert selected.score == pytest.approx(expected)


def test_default_maximum_excludes_six_board_candidates():
    selected = select_board(1800, 1200, detail_score=1.0)

    assert selected.board_count <= 4


def test_exact_score_tie_uses_declared_candidate_order():
    source_aspect = math.sqrt(2 * math.exp(0.08))

    selected = select_board(source_aspect, 1, detail_score=0.2)

    assert (selected.width, selected.height) == (29, 29)


@pytest.mark.parametrize("subject_width", [0, -1, math.inf, math.nan])
def test_subject_width_must_be_positive_and_finite(subject_width):
    with pytest.raises(ValueError, match="subject_width must be a finite positive number"):
        select_board(subject_width, 1000)


def test_max_boards_must_allow_at_least_one_board():
    with pytest.raises(ValueError, match="max_boards must be a positive integer"):
        select_board(1000, 1000, max_boards=0)


@pytest.mark.parametrize(
    ("subject_width", "subject_height", "expected_dimensions"),
    [
        (sys.float_info.max, 5e-324, (58, 29)),
        (5e-324, sys.float_info.max, (29, 58)),
    ],
)
def test_extreme_finite_subject_dimensions_select_a_finite_score(
    subject_width, subject_height, expected_dimensions
):
    try:
        selected = select_board(subject_width, subject_height)
    except (ValueError, ZeroDivisionError) as error:
        pytest.fail(f"finite positive dimensions must not fail: {error}")

    assert (selected.width, selected.height) == expected_dimensions
    assert math.isfinite(selected.score)


def test_layout_boards_preserves_nonstandard_pattern_dimensions():
    layout = layout_boards(68, 60)

    assert layout == BoardLayout(
        pattern_width=68,
        pattern_height=60,
        module_size=29,
        board_columns=3,
        board_rows=3,
    )


def test_partial_board_pattern_validates_against_derived_layout():
    layout = layout_boards(68, 60)
    pattern = Pattern(
        width=layout.pattern_width,
        height=layout.pattern_height,
        module_size=layout.module_size,
        palette=[],
        cells=[[None] * layout.pattern_width for _ in range(layout.pattern_height)],
        verification=VerificationState.VERIFIED,
        board_columns=layout.board_columns,
        board_rows=layout.board_rows,
        is_custom_size=True,
    )

    pattern.validate()


def test_custom_partial_board_pattern_renders_all_internal_module_seams():
    layout = layout_boards(68, 60)
    pattern = Pattern(
        width=layout.pattern_width,
        height=layout.pattern_height,
        module_size=layout.module_size,
        palette=[],
        cells=[[None] * layout.pattern_width for _ in range(layout.pattern_height)],
        verification=VerificationState.VERIFIED,
        board_columns=layout.board_columns,
        board_rows=layout.board_rows,
        is_custom_size=True,
    )

    image = render_template(pattern, cell_size=4)

    for column in (29, 58):
        assert image.getpixel((GRID_LEFT + column * 4, GRID_TOP + 1))[:3] == BOARD_GRID
    for row in (29, 58):
        assert image.getpixel((GRID_LEFT + 1, GRID_TOP + row * 4))[:3] == BOARD_GRID
