"""Standard fuse-bead board selection."""

from dataclasses import dataclass
import math
from numbers import Real


MODULE_SIZE = 29
STANDARD_CANDIDATES = (
    (29, 29),
    (58, 29),
    (29, 58),
    (58, 58),
    (87, 58),
    (58, 87),
)
_CLOSE_SCORE_DELTA = 0.05
_TIE_TOLERANCE = 1e-12


@dataclass(frozen=True)
class BoardSelection:
    width: int
    height: int
    board_columns: int
    board_rows: int
    is_custom: bool
    requires_confirmation: bool
    score: float
    alternatives: tuple[tuple[int, int], ...]

    @property
    def board_count(self) -> int:
        return self.board_columns * self.board_rows


def select_board(
    subject_width: Real,
    subject_height: Real,
    detail_score: Real = 0.5,
    explicit_size: tuple[int, int] | None = None,
    max_boards: int = 4,
) -> BoardSelection:
    """Select the lowest-scoring standard board arrangement.

    ``max_boards`` limits automatic candidates.  An explicit grid size always
    takes precedence and is therefore not constrained by that preference.
    """
    _validate_positive_finite_number(subject_width, "subject_width")
    _validate_positive_finite_number(subject_height, "subject_height")
    _validate_nonnegative_finite_number(detail_score, "detail_score")
    _validate_positive_integer(max_boards, "max_boards")

    if explicit_size is not None:
        width, height = _validate_explicit_size(explicit_size)
        board_columns = _board_modules(width)
        board_rows = _board_modules(height)
        board_count = board_columns * board_rows
        return BoardSelection(
            width=width,
            height=height,
            board_columns=board_columns,
            board_rows=board_rows,
            is_custom=(width, height) not in STANDARD_CANDIDATES,
            requires_confirmation=board_count > 4,
            score=0.0,
            alternatives=(),
        )

    source_aspect = float(subject_width) / float(subject_height)
    candidates = []
    for index, (width, height) in enumerate(STANDARD_CANDIDATES):
        board_columns = width // MODULE_SIZE
        board_rows = height // MODULE_SIZE
        board_count = board_columns * board_rows
        if board_count > max_boards:
            continue
        score = _candidate_score(
            width=width,
            height=height,
            source_aspect=source_aspect,
            detail_score=float(detail_score),
            board_count=board_count,
        )
        candidates.append((index, width, height, board_columns, board_rows, score))

    lowest_score = min(candidate[-1] for candidate in candidates)
    selected = next(
        candidate
        for candidate in candidates
        if math.isclose(candidate[-1], lowest_score, rel_tol=0.0, abs_tol=_TIE_TOLERANCE)
    )
    _, width, height, board_columns, board_rows, score = selected
    alternatives = tuple(
        (candidate[1], candidate[2])
        for candidate in candidates
        if (candidate[1], candidate[2]) != (width, height)
        and abs(candidate[-1] - score) <= _CLOSE_SCORE_DELTA
    )
    board_count = board_columns * board_rows
    return BoardSelection(
        width=width,
        height=height,
        board_columns=board_columns,
        board_rows=board_rows,
        is_custom=False,
        requires_confirmation=board_count > 4,
        score=score,
        alternatives=alternatives,
    )


def _candidate_score(
    *,
    width: int,
    height: int,
    source_aspect: float,
    detail_score: float,
    board_count: int,
) -> float:
    aspect_loss = abs(math.log((width / height) / source_aspect))
    detail_penalty = max(0.0, detail_score - min(width, height) / 58)
    board_penalty = 0.08 * max(0, board_count - 1)
    return aspect_loss + detail_penalty + board_penalty


def _board_modules(size: int) -> int:
    return math.ceil(size / MODULE_SIZE)


def _validate_explicit_size(explicit_size: tuple[int, int]) -> tuple[int, int]:
    if not isinstance(explicit_size, tuple) or len(explicit_size) != 2:
        raise ValueError("explicit_size must be a pair of positive integers")
    width, height = explicit_size
    if not _is_positive_integer(width) or not _is_positive_integer(height):
        raise ValueError("explicit_size must be a pair of positive integers")
    return width, height


def _validate_positive_finite_number(value: object, name: str) -> None:
    if not _is_finite_number(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")


def _validate_nonnegative_finite_number(value: object, name: str) -> None:
    if not _is_finite_number(value) or value < 0:
        raise ValueError(f"{name} must be a finite nonnegative number")


def _validate_positive_integer(value: object, name: str) -> None:
    if not _is_positive_integer(value):
        raise ValueError(f"{name} must be a positive integer")


def _is_finite_number(value: object) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)


def _is_positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
