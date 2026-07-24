"""Canonical data structures for Fuse Bead Designer."""

from .boards import BoardLayout, layout_boards
from .logical_grid import AmbiguousGridError, GridSpec, recover_nearest_neighbor_grid
from .models import CompileReport, PaletteColor, Pattern, VerificationState
from .quantize import sample_cell_centers
from .routing import RoutePolicy, policy_for
from .sizing import PatternSizeCandidate, recommend_pattern_sizes

__all__ = [
    "AmbiguousGridError",
    "BoardLayout",
    "CompileReport",
    "GridSpec",
    "PaletteColor",
    "Pattern",
    "PatternSizeCandidate",
    "RoutePolicy",
    "VerificationState",
    "layout_boards",
    "policy_for",
    "recover_nearest_neighbor_grid",
    "recommend_pattern_sizes",
    "sample_cell_centers",
]
