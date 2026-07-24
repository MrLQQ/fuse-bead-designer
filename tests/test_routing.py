from dataclasses import FrozenInstanceError

import pytest

from fuse_bead_designer.routing import RoutePolicy, policy_for


@pytest.mark.parametrize("classification", ["pixel-art", "pattern-draft"])
def test_grid_source_routes_require_declared_or_recovered_grid(classification):
    policy = policy_for(classification)

    assert policy == RoutePolicy(
        classification=classification,
        requires_pattern_draft=False,
        requires_declared_grid=True,
        sampling="center",
        cleanup=False,
        crop_subject=False,
    )


def test_route_policy_is_immutable():
    policy = policy_for("pixel-art")

    with pytest.raises(FrozenInstanceError):
        policy.sampling = "median"


def test_finished_bead_photo_requires_a_rectified_grid():
    with pytest.raises(ValueError, match="rectified_grid=True"):
        policy_for("finished-bead-photo")


def test_rectified_finished_bead_photo_uses_center_sampling_without_cleanup():
    policy = policy_for("finished-bead-photo", rectified_grid=True)

    assert policy == RoutePolicy(
        classification="finished-bead-photo",
        requires_pattern_draft=False,
        requires_declared_grid=True,
        sampling="center",
        cleanup=False,
        crop_subject=False,
    )


def test_high_resolution_image_requires_pattern_draft():
    with pytest.raises(ValueError, match="has_pattern_draft=True"):
        policy_for("high-resolution-image")


def test_high_resolution_image_with_draft_uses_center_sampling_without_cleanup():
    policy = policy_for("high-resolution-image", has_pattern_draft=True)

    assert policy == RoutePolicy(
        classification="high-resolution-image",
        requires_pattern_draft=True,
        requires_declared_grid=False,
        sampling="center",
        cleanup=False,
        crop_subject=False,
    )


@pytest.mark.parametrize(
    ("classification", "legacy_resample"),
    [
        ("unclassified", False),
        ("pixel-art", True),
        ("finished-bead-photo", True),
        ("high-resolution-image", True),
    ],
)
def test_compatibility_routes_use_median_sampling_and_cleanup(
    classification, legacy_resample
):
    policy = policy_for(classification, legacy_resample=legacy_resample)

    assert policy == RoutePolicy(
        classification=classification,
        requires_pattern_draft=False,
        requires_declared_grid=False,
        sampling="median",
        cleanup=True,
        crop_subject=True,
    )


def test_unsupported_classification_is_rejected():
    with pytest.raises(ValueError, match="unsupported classification"):
        policy_for("watercolor")
