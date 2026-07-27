import csv
import json
from pathlib import Path

from PIL import Image
import pytest

from fuse_bead_designer.variant_set import (
    render_variant_comparison,
    validate_feature_contract,
    validate_variant_set,
)


FEATURE_CONTRACT = {
    "subject": "red travel mug",
    "features": [
        {
            "id": "handle",
            "description": "open handle on the right",
            "importance": "hard",
        },
        {
            "id": "highlight",
            "description": "small highlight on the body",
            "importance": "soft",
        },
    ],
}


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _build_valid_variant_fixture(
    root: Path,
    names: tuple[str, ...] = ("economy", "baseline"),
) -> Path:
    _write_json(root / "feature-contract.json", FEATURE_CONTRACT)
    for index, name in enumerate(names, start=1):
        variant = root / name
        artifacts = variant / "artifacts"
        artifacts.mkdir(parents=True)
        verification = "verified" if name == "baseline" else "review-required"
        cells = [["red"] * index]
        manifest = {
            "name": name,
            "width": index,
            "height": 1,
            "attempt": 1,
            "verification": verification,
            "feature_results": {"handle": True, "highlight": index > 1},
            "artifacts": "artifacts",
        }
        pattern = {
            "width": index,
            "height": 1,
            "module_size": 29,
            "board_layout": {"columns": 1, "rows": 1, "is_custom_size": True},
            "palette": [
                {
                    "id": "red",
                    "name": "Red",
                    "name_zh": "红色",
                    "hex": "#E53935",
                    "brand_code": None,
                }
            ],
            "cells": cells,
            "total_beads": index,
            "color_counts": {"red": index},
            "verification": verification,
            "inferred_cells": [],
            "settings": {},
        }
        _write_json(variant / "manifest.json", manifest)
        _write_json(artifacts / "pattern.json", pattern)
        with (artifacts / "colors.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=("id", "name", "name_zh", "hex", "brand_code", "count"),
            )
            writer.writeheader()
            writer.writerow(
                {
                    "id": "red",
                    "name": "Red",
                    "name_zh": "红色",
                    "hex": "#E53935",
                    "brand_code": "",
                    "count": index,
                }
            )
        Image.new("RGB", (2, 2), "#E53935").save(artifacts / "template.png")
        Image.new("RGB", (2, 2), "#FFFFFF").save(artifacts / "review.png")
    return root


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_feature_contract_accepts_generic_non_human_features():
    contract = validate_feature_contract(FEATURE_CONTRACT)

    assert contract["subject"] == "red travel mug"
    assert [feature["id"] for feature in contract["features"]] == [
        "handle",
        "highlight",
    ]


@pytest.mark.parametrize(
    "contract",
    [
        {"subject": "mug", "features": []},
        {
            "subject": "mug",
            "features": [
                {"id": "handle", "description": "a", "importance": "hard"},
                {"id": "handle", "description": "b", "importance": "soft"},
            ],
        },
        {
            "subject": "mug",
            "features": [
                {"id": "handle", "description": "a", "importance": "optional"}
            ],
        },
    ],
)
def test_feature_contract_rejects_missing_duplicate_or_invalid_features(contract):
    with pytest.raises(ValueError):
        validate_feature_contract(contract)


def test_variant_set_accepts_two_to_four_compiled_semantic_versions(tmp_path):
    root = _build_valid_variant_fixture(tmp_path)

    summary = validate_variant_set(root)

    assert [item["name"] for item in summary["variants"]] == [
        "economy",
        "baseline",
    ]
    assert summary["recommended"] == "economy"


def test_variant_set_prefers_balanced_when_present(tmp_path):
    root = _build_valid_variant_fixture(
        tmp_path,
        names=("economy", "balanced", "detail", "baseline"),
    )

    assert validate_variant_set(root)["recommended"] == "balanced"


def test_variant_set_rejects_an_accepted_variant_missing_a_hard_feature(tmp_path):
    root = _build_valid_variant_fixture(tmp_path)
    manifest_path = root / "economy" / "manifest.json"
    manifest = _load_json(manifest_path)
    manifest["feature_results"]["handle"] = False
    _write_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="hard feature handle failed"):
        validate_variant_set(root)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("attempt", "attempt must be 1 or 2"),
        ("duplicate", "duplicate variant name"),
    ],
)
def test_variant_set_rejects_more_than_two_attempts_and_duplicate_tiers(
    tmp_path,
    mutation,
    message,
):
    root = _build_valid_variant_fixture(tmp_path)
    manifest_path = root / "economy" / "manifest.json"
    manifest = _load_json(manifest_path)
    if mutation == "attempt":
        manifest["attempt"] = 3
    else:
        manifest["name"] = "baseline"
    _write_json(manifest_path, manifest)

    with pytest.raises(ValueError, match=message):
        validate_variant_set(root)


def test_variant_set_recounts_pattern_and_csv_instead_of_trusting_manifest(tmp_path):
    root = _build_valid_variant_fixture(tmp_path)
    pattern_path = root / "economy" / "artifacts" / "pattern.json"
    pattern = _load_json(pattern_path)
    pattern["total_beads"] = 99
    _write_json(pattern_path, pattern)

    with pytest.raises(ValueError, match="total_beads"):
        validate_variant_set(root)


def test_variant_set_requires_review_for_semantic_redesigns(tmp_path):
    root = _build_valid_variant_fixture(tmp_path)
    manifest_path = root / "economy" / "manifest.json"
    manifest = _load_json(manifest_path)
    manifest["verification"] = "verified"
    _write_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="must be review-required"):
        validate_variant_set(root)


def test_variant_set_rejects_unreadable_png(tmp_path):
    root = _build_valid_variant_fixture(tmp_path)
    (root / "economy" / "artifacts" / "template.png").write_bytes(b"not a png")

    with pytest.raises(ValueError, match="unreadable PNG"):
        validate_variant_set(root)


def test_comparison_renderer_writes_a_valid_png(tmp_path):
    root = _build_valid_variant_fixture(tmp_path)
    summary = validate_variant_set(root)
    destination = tmp_path / "comparison.png"

    render_variant_comparison(summary, destination)

    with Image.open(destination) as image:
        image.verify()
