import math

import pytest

from fuse_bead_designer.sizing import (
    PatternSizeCandidate,
    expand_semantic_size_target,
    plan_semantic_size_targets,
    recommend_pattern_sizes,
)


def test_recommendations_offer_named_aspect_preserving_variants():
    landscape = recommend_pattern_sizes(4, 3, 0.5)
    portrait = recommend_pattern_sizes(3, 4, 0.5)

    assert tuple(candidate.name for candidate in landscape) == (
        "economy",
        "balanced",
        "detail",
    )
    assert all(isinstance(candidate, PatternSizeCandidate) for candidate in landscape)
    assert all(candidate.width == candidate.target_long_side for candidate in landscape)
    assert all(candidate.height == candidate.target_long_side for candidate in portrait)
    assert all(
        abs(candidate.height - candidate.target_long_side * 3 / 4) <= 1
        for candidate in landscape
    )
    assert all(
        abs(candidate.width - candidate.target_long_side * 3 / 4) <= 1
        for candidate in portrait
    )


def test_recommendations_are_not_restricted_to_board_multiples():
    candidates = recommend_pattern_sizes(4, 3, 0.5)

    assert any(
        candidate.width % 29 != 0 or candidate.height % 29 != 0
        for candidate in candidates
    )


def test_recommendation_size_increases_monotonically_with_detail_score():
    low = recommend_pattern_sizes(16, 9, 0.0)
    medium = recommend_pattern_sizes(16, 9, 0.5)
    high = recommend_pattern_sizes(16, 9, 1.0)

    assert [candidate.target_long_side for candidate in low] == [48, 64, 80]
    assert [candidate.target_long_side for candidate in medium] == [56, 72, 88]
    assert [candidate.target_long_side for candidate in high] == [64, 80, 96]
    assert all(
        low_candidate.target_long_side
        < medium_candidate.target_long_side
        < high_candidate.target_long_side
        for low_candidate, medium_candidate, high_candidate in zip(low, medium, high)
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("subject_width", 0),
        ("subject_width", -1),
        ("subject_width", math.inf),
        ("subject_width", math.nan),
        ("subject_height", 0),
        ("subject_height", -1),
        ("subject_height", math.inf),
        ("subject_height", math.nan),
    ],
)
def test_recommendations_require_finite_positive_subject_dimensions(field, value):
    arguments = {"subject_width": 4, "subject_height": 3, "detail_score": 0.5}
    arguments[field] = value

    with pytest.raises(ValueError, match=f"{field} must be a finite positive number"):
        recommend_pattern_sizes(**arguments)


@pytest.mark.parametrize("detail_score", [-0.1, 1.1, math.inf, math.nan])
def test_recommendations_require_normalized_finite_detail_score(detail_score):
    with pytest.raises(ValueError, match="detail_score must be a finite number between 0 and 1"):
        recommend_pattern_sizes(4, 3, detail_score)


def test_semantic_targets_span_minimum_to_baseline_without_board_multiples():
    targets = plan_semantic_size_targets(132, 144, 63)

    assert [target.name for target in targets] == ["economy", "balanced", "detail"]
    assert [target.target_long_side for target in targets] == [63, 104, 128]
    assert all(target.width < 132 and target.height < 144 for target in targets)
    assert any(target.width % 29 or target.height % 29 for target in targets)


def test_semantic_targets_deduplicate_when_the_feasible_span_is_small():
    targets = plan_semantic_size_targets(20, 21, 18)

    assert len({(target.width, target.height) for target in targets}) == len(targets)
    assert len(targets) < 3


def test_semantic_retry_expands_once_but_never_reaches_past_baseline():
    target = plan_semantic_size_targets(132, 144, 63)[0]

    retry = expand_semantic_size_target(target, 132, 144)

    assert retry is not None
    assert retry.attempt == 2
    assert retry.target_long_side > target.target_long_side
    assert expand_semantic_size_target(retry, 132, 144) is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("baseline_width", True),
        ("baseline_width", 0),
        ("baseline_width", 3.5),
        ("baseline_height", False),
        ("baseline_height", -1),
        ("baseline_height", 8.5),
        ("minimum_long_side", True),
        ("minimum_long_side", 0),
        ("minimum_long_side", 5.5),
    ],
)
def test_semantic_targets_require_positive_integer_dimensions(field, value):
    arguments = {
        "baseline_width": 132,
        "baseline_height": 144,
        "minimum_long_side": 63,
    }
    arguments[field] = value

    with pytest.raises(ValueError, match=f"{field} must be a positive integer"):
        plan_semantic_size_targets(**arguments)


def test_semantic_target_minimum_must_be_smaller_than_baseline():
    with pytest.raises(ValueError, match="minimum_long_side must be smaller"):
        plan_semantic_size_targets(20, 21, 21)
