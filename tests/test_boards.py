import math

import pytest

from fuse_bead_designer.boards import STANDARD_CANDIDATES, select_board


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


def test_balanced_subject_exposes_only_standard_close_alternatives():
    selected = select_board(1500, 1000, detail_score=0.2)

    assert selected.alternatives
    assert (selected.width, selected.height) not in selected.alternatives
    assert all(candidate in STANDARD_CANDIDATES for candidate in selected.alternatives)


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
