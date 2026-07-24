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


def _scaled_short_side(target_long_side: int, source_short: int, source_long: int) -> int:
    numerator = target_long_side * source_short
    rounded = (2 * numerator + source_long) // (2 * source_long)
    return max(1, rounded)


def _validate_positive_integer(value: object, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")


def _validate_detail_score(value: object) -> None:
    if (
        not isinstance(value, Real)
        or isinstance(value, bool)
        or not math.isfinite(value)
        or not 0 <= value <= 1
    ):
        raise ValueError("detail_score must be a finite number between 0 and 1")
