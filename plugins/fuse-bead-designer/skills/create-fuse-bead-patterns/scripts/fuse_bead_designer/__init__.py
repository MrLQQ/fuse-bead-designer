"""Canonical data structures for Fuse Bead Designer."""

from .boards import BoardLayout, layout_boards
from .models import CompileReport, PaletteColor, Pattern, VerificationState
from .sizing import PatternSizeCandidate, recommend_pattern_sizes

__all__ = [
    "BoardLayout",
    "CompileReport",
    "PaletteColor",
    "Pattern",
    "PatternSizeCandidate",
    "VerificationState",
    "layout_boards",
    "recommend_pattern_sizes",
]
