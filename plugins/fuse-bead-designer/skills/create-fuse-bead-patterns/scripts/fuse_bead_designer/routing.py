"""Source-class routing policies for pattern compilation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RoutePolicy:
    classification: str
    requires_pattern_draft: bool
    requires_declared_grid: bool
    sampling: str
    cleanup: bool
    crop_subject: bool


_SUPPORTED_CLASSIFICATIONS = frozenset(
    {
        "pixel-art",
        "pattern-draft",
        "finished-bead-photo",
        "high-resolution-image",
        "unclassified",
    }
)


def policy_for(
    classification: str,
    *,
    rectified_grid: bool = False,
    has_pattern_draft: bool = False,
    legacy_resample: bool = False,
) -> RoutePolicy:
    """Return the processing policy allowed for a classified source."""
    if classification not in _SUPPORTED_CLASSIFICATIONS:
        raise ValueError(f"unsupported classification: {classification}")

    if classification == "unclassified" or legacy_resample:
        return RoutePolicy(
            classification=classification,
            requires_pattern_draft=False,
            requires_declared_grid=False,
            sampling="median",
            cleanup=True,
            crop_subject=True,
        )

    if classification == "finished-bead-photo" and not rectified_grid:
        raise ValueError(
            "finished-bead-photo requires rectified_grid=True before compilation"
        )
    if classification == "high-resolution-image" and not has_pattern_draft:
        raise ValueError(
            "high-resolution-image requires has_pattern_draft=True before compilation"
        )

    if classification in {"pixel-art", "pattern-draft", "finished-bead-photo"}:
        return RoutePolicy(
            classification=classification,
            requires_pattern_draft=False,
            requires_declared_grid=True,
            sampling="center",
            cleanup=False,
            crop_subject=False,
        )

    return RoutePolicy(
        classification=classification,
        requires_pattern_draft=True,
        requires_declared_grid=False,
        sampling="center",
        cleanup=False,
        crop_subject=False,
    )
