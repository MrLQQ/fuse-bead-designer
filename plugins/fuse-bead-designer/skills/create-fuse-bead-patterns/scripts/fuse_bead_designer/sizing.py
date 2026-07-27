"""Pattern-size recommendations independent from physical board layout."""

from dataclasses import dataclass
import math
from numbers import Real


_LONG_SIDE_ANCHORS = (("economy", 48), ("balanced", 64), ("detail", 80))
_MAX_DETAIL_ADJUSTMENT = 16


@dataclass(frozen=True)
class PatternSizeCandidate:
    name: str
    width: int
    height: int
    target_long_side: int


@dataclass(frozen=True)
class SemanticSizeTarget:
    """Advisory canvas for one independently redrawn semantic variant."""

    name: str
    width: int
    height: int
    target_long_side: int
    attempt: int = 1


def recommend_pattern_sizes(
    subject_width: int,
    subject_height: int,
    detail_score: float,
) -> tuple[PatternSizeCandidate, ...]:
    """Return aspect-preserving advisory logical-grid sizes."""
    _validate_positive_integer(subject_width, "subject_width")
    _validate_positive_integer(subject_height, "subject_height")
    _validate_detail_score(detail_score)

    adjustment = round(float(detail_score) * _MAX_DETAIL_ADJUSTMENT)
    candidates = []
    for name, anchor in _LONG_SIDE_ANCHORS:
        target_long_side = anchor + adjustment
        short_side = _scaled_short_side(
            target_long_side,
            min(subject_width, subject_height),
            max(subject_width, subject_height),
        )
        if subject_width >= subject_height:
            width, height = target_long_side, short_side
        else:
            width, height = short_side, target_long_side
        candidates.append(
            PatternSizeCandidate(
                name=name,
                width=width,
                height=height,
                target_long_side=target_long_side,
            )
        )
    return tuple(candidates)


def plan_semantic_size_targets(
    baseline_width: int,
    baseline_height: int,
    minimum_long_side: int,
) -> tuple[SemanticSizeTarget, ...]:
    """Plan economy-to-detail redraw targets below a completed baseline."""
    _validate_semantic_dimension(baseline_width, "baseline_width")
    _validate_semantic_dimension(baseline_height, "baseline_height")
    _validate_semantic_dimension(minimum_long_side, "minimum_long_side")

    baseline_long_side = max(baseline_width, baseline_height)
    if minimum_long_side >= baseline_long_side:
        raise ValueError("minimum_long_side must be smaller than the baseline long side")

    span = baseline_long_side - minimum_long_side
    target_specs = (
        ("economy", minimum_long_side),
        ("balanced", minimum_long_side + _round_fraction_half_up(span, 1, 2)),
        ("detail", minimum_long_side + _round_fraction_half_up(span, 4, 5)),
    )
    targets = []
    seen_dimensions = set()
    for name, target_long_side in target_specs:
        if target_long_side >= baseline_long_side:
            continue
        width, height = _scale_from_baseline(
            target_long_side,
            baseline_width,
            baseline_height,
        )
        dimensions = (width, height)
        if dimensions in seen_dimensions:
            continue
        seen_dimensions.add(dimensions)
        targets.append(
            SemanticSizeTarget(
                name=name,
                width=width,
                height=height,
                target_long_side=target_long_side,
            )
        )
    return tuple(targets)


def expand_semantic_size_target(
    target: SemanticSizeTarget,
    baseline_width: int,
    baseline_height: int,
) -> SemanticSizeTarget | None:
    """Return the single allowed larger retry, or None when none is valid."""
    if not isinstance(target, SemanticSizeTarget):
        raise ValueError("target must be a SemanticSizeTarget")
    _validate_semantic_dimension(baseline_width, "baseline_width")
    _validate_semantic_dimension(baseline_height, "baseline_height")
    if target.attempt != 1:
        return None

    baseline_long_side = max(baseline_width, baseline_height)
    growth = max(2, math.ceil(target.target_long_side * 0.10))
    expanded_long_side = min(target.target_long_side + growth, baseline_long_side - 1)
    if expanded_long_side <= target.target_long_side:
        return None
    width, height = _scale_from_baseline(
        expanded_long_side,
        baseline_width,
        baseline_height,
    )
    return SemanticSizeTarget(
        name=target.name,
        width=width,
        height=height,
        target_long_side=expanded_long_side,
        attempt=2,
    )


def _scale_from_baseline(
    target_long_side: int,
    baseline_width: int,
    baseline_height: int,
) -> tuple[int, int]:
    short_side = _scaled_short_side(
        target_long_side,
        min(baseline_width, baseline_height),
        max(baseline_width, baseline_height),
    )
    if baseline_width >= baseline_height:
        return target_long_side, short_side
    return short_side, target_long_side


def _round_fraction_half_up(value: int, numerator: int, denominator: int) -> int:
    scaled = value * numerator
    return (2 * scaled + denominator) // (2 * denominator)


def _scaled_short_side(target_long_side: int, source_short: int, source_long: int) -> int:
    numerator = target_long_side * source_short
    rounded = (2 * numerator + source_long) // (2 * source_long)
    return max(1, rounded)


def _validate_positive_integer(value: object, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")


def _validate_semantic_dimension(value: object, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_detail_score(value: object) -> None:
    if (
        not isinstance(value, Real)
        or isinstance(value, bool)
        or not math.isfinite(value)
        or not 0 <= value <= 1
    ):
        raise ValueError("detail_score must be a finite number between 0 and 1")
