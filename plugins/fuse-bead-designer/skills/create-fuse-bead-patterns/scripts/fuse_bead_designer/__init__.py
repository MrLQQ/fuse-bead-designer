"""Canonical data structures for Fuse Bead Designer."""

from .boards import BoardLayout, layout_boards
from .models import CompileReport, PaletteColor, Pattern, VerificationState
from .routing import RoutePolicy, policy_for
from .sizing import PatternSizeCandidate, recommend_pattern_sizes

__all__ = [
    "BoardLayout",
    "CompileReport",
    "PaletteColor",
    "Pattern",
    "PatternSizeCandidate",
    "RoutePolicy",
    "VerificationState",
    "layout_boards",
    "policy_for",
    "recommend_pattern_sizes",
]
