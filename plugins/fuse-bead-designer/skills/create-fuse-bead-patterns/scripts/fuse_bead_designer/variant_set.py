"""Validate and present independently compiled semantic size variants."""

from collections import Counter
import csv
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError


_TIER_ORDER = ("economy", "balanced", "detail", "baseline")
_FONT_PATH = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "fonts"
    / "NotoSansCJKsc-Regular.otf"
)


def validate_feature_contract(data: object) -> dict[str, object]:
    """Validate a task-specific, content-agnostic semantic feature contract."""
    if not isinstance(data, dict):
        raise ValueError("feature contract must be an object")
    subject = data.get("subject")
    features = data.get("features")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("feature contract subject must be a non-empty string")
    if not isinstance(features, list) or not features:
        raise ValueError("feature contract features must be a non-empty list")

    seen = set()
    normalized = []
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError("feature contract entry must be an object")
        feature_id = feature.get("id")
        description = feature.get("description")
        importance = feature.get("importance")
        if not isinstance(feature_id, str) or not feature_id.strip():
            raise ValueError("feature id must be a non-empty string")
        if feature_id in seen:
            raise ValueError(f"duplicate feature id: {feature_id}")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"feature {feature_id} description must be non-empty")
        if importance not in {"hard", "soft"}:
            raise ValueError(f"feature {feature_id} importance must be hard or soft")
        seen.add(feature_id)
        normalized.append(
            {
                "id": feature_id,
                "description": description,
                "importance": importance,
            }
        )
    return {"subject": subject, "features": normalized}


def validate_variant_set(root: str | Path) -> dict[str, object]:
    """Recount compiler artifacts and validate two to four accepted variants."""
    variants_root = Path(root)
    contract = validate_feature_contract(
        _read_json(variants_root / "feature-contract.json")
    )
    variant_dirs = [
        path
        for path in variants_root.iterdir()
        if path.is_dir() and (path / "manifest.json").is_file()
    ]
    if not 2 <= len(variant_dirs) <= 4:
        raise ValueError("variant set must contain two to four accepted variants")

    manifests = [(path, _read_json(path / "manifest.json")) for path in variant_dirs]
    manifest_names = [
        manifest.get("name") if isinstance(manifest, dict) else None
        for _, manifest in manifests
    ]
    if len(set(manifest_names)) != len(manifest_names):
        raise ValueError("duplicate variant name")
    if set(manifest_names) - set(_TIER_ORDER):
        raise ValueError("variant name must be economy, balanced, detail, or baseline")
    if "baseline" not in manifest_names:
        raise ValueError("variant set must include baseline")

    manifest_by_name = {manifest["name"]: (path, manifest) for path, manifest in manifests}
    ordered_names = [name for name in _TIER_ORDER if name in manifest_by_name]
    hard_features = {
        feature["id"]
        for feature in contract["features"]
        if feature["importance"] == "hard"
    }
    all_features = {feature["id"] for feature in contract["features"]}
    variants = []
    for name in ordered_names:
        variant_dir, manifest = manifest_by_name[name]
        if variant_dir.name != name:
            raise ValueError(f"variant directory and manifest name disagree: {name}")
        variants.append(
            _validate_variant(
                variant_dir,
                manifest,
                all_features=all_features,
                hard_features=hard_features,
            )
        )

    for previous, current in zip(variants, variants[1:]):
        if current["long_side"] <= previous["long_side"]:
            raise ValueError("accepted variants must increase in long-side size")
        if current["total_beads"] <= previous["total_beads"]:
            raise ValueError("accepted variants must increase in bead count")

    non_baseline = [variant for variant in variants if variant["name"] != "baseline"]
    if any(variant["name"] == "balanced" for variant in non_baseline):
        recommended = "balanced"
    elif non_baseline:
        recommended = non_baseline[(len(non_baseline) - 1) // 2]["name"]
    else:
        recommended = variants[0]["name"]
    return {
        "feature_contract": contract,
        "recommended": recommended,
        "variants": variants,
    }


def render_variant_comparison(
    summary: dict[str, object],
    destination: str | Path,
) -> None:
    """Render display-only previews without changing logical pattern data."""
    variants = summary.get("variants")
    if not isinstance(variants, list) or not variants:
        raise ValueError("summary variants must be a non-empty list")

    panel_width = 430
    panel_height = 560
    gap = 24
    margin = 32
    canvas = Image.new(
        "RGB",
        (
            margin * 2 + panel_width * len(variants) + gap * (len(variants) - 1),
            panel_height + margin * 2,
        ),
        "#EEF1EF",
    )
    draw = ImageDraw.Draw(canvas)
    title_font = _font(25)
    detail_font = _font(17)
    for index, variant in enumerate(variants):
        left = margin + index * (panel_width + gap)
        top = margin
        draw.rounded_rectangle(
            (left, top, left + panel_width, top + panel_height),
            radius=18,
            fill="#FFFFFF",
            outline="#CDD3CF",
            width=2,
        )
        template_path = Path(variant["template"])
        with Image.open(template_path) as source:
            preview = source.convert("RGB")
        preview.thumbnail((panel_width - 36, 420), Image.Resampling.LANCZOS)
        preview_left = left + (panel_width - preview.width) // 2
        preview_top = top + 58 + (420 - preview.height) // 2
        canvas.paste(preview, (preview_left, preview_top))
        draw.text(
            (left + 20, top + 18),
            f"{variant['name']} · {variant['width']}×{variant['height']}",
            font=title_font,
            fill="#1D2522",
        )
        draw.text(
            (left + 20, top + 492),
            (
                f"{variant['total_beads']:,} 颗 · "
                f"{variant['board_columns']}×{variant['board_rows']} 底板"
            ),
            font=detail_font,
            fill="#313A36",
        )
        draw.text(
            (left + 20, top + 522),
            str(variant["verification"]),
            font=detail_font,
            fill="#725329",
        )

    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def _validate_variant(
    variant_dir: Path,
    manifest: object,
    *,
    all_features: set[str],
    hard_features: set[str],
) -> dict[str, object]:
    if not isinstance(manifest, dict):
        raise ValueError(f"{variant_dir.name} manifest must be an object")
    name = manifest["name"]
    attempt = manifest.get("attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt not in {1, 2}:
        raise ValueError(f"{name} attempt must be 1 or 2")
    width = _positive_integer(manifest.get("width"), f"{name} width")
    height = _positive_integer(manifest.get("height"), f"{name} height")
    verification = manifest.get("verification")
    if name != "baseline" and verification != "review-required":
        raise ValueError(f"{name} must be review-required")
    if verification not in {"verified", "review-required"}:
        raise ValueError(f"{name} verification is invalid")

    feature_results = manifest.get("feature_results")
    if not isinstance(feature_results, dict) or set(feature_results) != all_features:
        raise ValueError(f"{name} feature_results must cover the feature contract")
    if any(not isinstance(result, bool) for result in feature_results.values()):
        raise ValueError(f"{name} feature results must be Boolean")
    for feature_id in hard_features:
        if feature_results[feature_id] is not True:
            raise ValueError(f"hard feature {feature_id} failed in {name}")

    artifacts_value = manifest.get("artifacts")
    if (
        not isinstance(artifacts_value, str)
        or not artifacts_value
        or Path(artifacts_value).is_absolute()
        or ".." in Path(artifacts_value).parts
    ):
        raise ValueError(f"{name} artifacts must be a safe relative path")
    artifacts = variant_dir / artifacts_value
    pattern = _read_json(artifacts / "pattern.json")
    if not isinstance(pattern, dict):
        raise ValueError(f"{name} pattern must be an object")
    if pattern.get("width") != width or pattern.get("height") != height:
        raise ValueError(f"{name} manifest dimensions disagree with pattern")
    if pattern.get("verification") != verification:
        raise ValueError(f"{name} verification disagrees with pattern")
    if pattern.get("module_size") != 29:
        raise ValueError(f"{name} module_size must be 29")

    cells = pattern.get("cells")
    if (
        not isinstance(cells, list)
        or len(cells) != height
        or any(not isinstance(row, list) or len(row) != width for row in cells)
    ):
        raise ValueError(f"{name} cells disagree with pattern dimensions")
    recounted = dict(
        sorted(Counter(cell for row in cells for cell in row if cell is not None).items())
    )
    if pattern.get("color_counts") != recounted:
        raise ValueError(f"{name} color_counts disagree with cells")
    total_beads = sum(recounted.values())
    if pattern.get("total_beads") != total_beads:
        raise ValueError(f"{name} total_beads disagree with cells")
    if _read_csv_counts(artifacts / "colors.csv") != recounted:
        raise ValueError(f"{name} colors.csv disagrees with cells")

    board_layout = pattern.get("board_layout")
    if not isinstance(board_layout, dict):
        raise ValueError(f"{name} board_layout must be an object")
    expected_columns = math.ceil(width / 29)
    expected_rows = math.ceil(height / 29)
    if (
        board_layout.get("columns") != expected_columns
        or board_layout.get("rows") != expected_rows
    ):
        raise ValueError(f"{name} board_layout disagrees with 29 x 29 coverage")

    template = artifacts / "template.png"
    _verify_png(template, name)
    review = artifacts / "review.png"
    if verification == "review-required" or review.exists():
        _verify_png(review, name)
    return {
        "name": name,
        "width": width,
        "height": height,
        "long_side": max(width, height),
        "attempt": attempt,
        "verification": verification,
        "total_beads": total_beads,
        "board_columns": expected_columns,
        "board_rows": expected_rows,
        "feature_results": feature_results,
        "template": str(template.resolve()),
        "review": str(review.resolve()) if review.exists() else None,
        "pattern": str((artifacts / "pattern.json").resolve()),
        "colors": str((artifacts / "colors.csv").resolve()),
    }


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON: {path}") from error


def _read_csv_counts(path: Path) -> dict[str, int]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        counts = {}
        for row in rows:
            count = int(row["count"])
            if count:
                counts[row["id"]] = count
        return dict(sorted(counts.items()))
    except (FileNotFoundError, KeyError, TypeError, ValueError) as error:
        raise ValueError(f"cannot read colors CSV: {path}") from error


def _verify_png(path: Path, name: str) -> None:
    try:
        with Image.open(path) as image:
            if image.format != "PNG":
                raise ValueError
            image.verify()
    except (FileNotFoundError, OSError, UnidentifiedImageError, ValueError) as error:
        raise ValueError(f"{name} has unreadable PNG: {path.name}") from error


def _positive_integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if _FONT_PATH.is_file():
        return ImageFont.truetype(str(_FONT_PATH), size)
    return ImageFont.load_default()
