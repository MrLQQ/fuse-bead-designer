"""Canonical data structures for Fuse Bead Designer."""

from .boards import BoardLayout, layout_boards
from .logical_grid import AmbiguousGridError, GridSpec, recover_nearest_neighbor_grid
from .models import CompileReport, PaletteColor, Pattern, VerificationState
from .quantize import sample_cell_centers
from .routing import RoutePolicy, policy_for
from .sizing import (
    PatternSizeCandidate,
    SemanticSizeTarget,
    expand_semantic_size_target,
    plan_semantic_size_targets,
    recommend_pattern_sizes,
)
from .variant_set import (
    render_variant_comparison,
    validate_feature_contract,
    validate_variant_set,
)

__all__ = [
    "AmbiguousGridError",
    "BoardLayout",
    "CompileReport",
    "GridSpec",
    "PaletteColor",
    "Pattern",
    "PatternSizeCandidate",
    "RoutePolicy",
    "SemanticSizeTarget",
    "VerificationState",
    "expand_semantic_size_target",
    "layout_boards",
    "plan_semantic_size_targets",
    "policy_for",
    "recover_nearest_neighbor_grid",
    "render_variant_comparison",
    "recommend_pattern_sizes",
    "sample_cell_centers",
    "validate_feature_contract",
    "validate_variant_set",
]
