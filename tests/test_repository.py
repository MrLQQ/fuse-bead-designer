import json
from pathlib import Path

from PIL import Image, ImageChops


def test_chinese_readme_is_primary():
    chinese = Path("README.md").read_text(encoding="utf-8")
    english = Path("README.en.md").read_text(encoding="utf-8")

    assert "[English](README.en.md)" in chinese
    assert "[中文](README.md)" in english
    assert "安装" in chinese


def test_readmes_put_natural_language_before_developer_cli():
    chinese = Path("README.md").read_text(encoding="utf-8")
    english = Path("README.en.md").read_text(encoding="utf-8")

    assert "请安装这个 Codex 插件：https://github.com/MrLQQ/fuse-bead-designer" in chinese
    assert "把这张图生成拼豆设计图" in chinese
    assert chinese.index("## 开发者") < chinese.index("python ")

    assert "Please install this Codex plugin: https://github.com/MrLQQ/fuse-bead-designer" in english
    assert "Turn the attached image into a fuse-bead pattern" in english
    assert english.index("## Developer") < english.index("python ")


def test_marketplace_points_to_plugin():
    data = json.loads(Path(".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    entry = next(item for item in data["plugins"] if item["name"] == "fuse-bead-designer")

    assert entry["source"]["path"] == "./plugins/fuse-bead-designer"


def test_remote_marketplace_has_collision_safe_name():
    data = json.loads(Path(".agents/plugins/marketplace.json").read_text(encoding="utf-8"))

    assert data["name"] == "fuse-bead-designer"
    assert data["interface"]["displayName"] == "Fuse Bead Designer"


def test_release_versions_are_synchronized():
    plugin = json.loads(
        Path("plugins/fuse-bead-designer/.codex-plugin/plugin.json").read_text(encoding="utf-8")
    )
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert plugin["version"] == "0.2.0"
    assert 'version = "0.2.0"' in pyproject


def test_agents_installation_contract_is_agent_owned():
    contract = Path("AGENTS.md").read_text(encoding="utf-8")

    assert "Request permission before installing anything." in contract
    assert "check whether the `fuse-bead-designer` Marketplace is already installed" in contract
    assert "Then separately check whether the `fuse-bead-designer` plugin is installed" in contract
    assert "If the Marketplace is not installed, run this command internally:" in contract
    assert "codex plugin marketplace add MrLQQ/fuse-bead-designer --ref v0.2.0" in contract
    assert "If the plugin is not installed, run this command internally:" in contract
    assert "codex plugin add fuse-bead-designer@fuse-bead-designer" in contract
    assert "Do not ask the user to run" in contract
    assert "new task" in contract
    assert "On compatible non-Codex hosts, use the standalone Release Skill" in contract
    assert "does not authorize cloning" in contract
    assert "running examples" in contract
    assert "creating virtual environments" in contract
    assert "installing runtime dependencies" in contract


def test_forward_eval_separates_installation_from_pattern_generation_rubrics():
    evaluation = Path("tests/skill-evals/with-skill.md").read_text(encoding="utf-8")

    assert "## Pattern-generation pass rubric" in evaluation
    assert "The installation-only scenario is evaluated only by the separate installation rubric below." in evaluation
    assert "## Installation-only pass rubric" in evaluation


def test_skill_eval_retains_real_pattern_quality_failure_baseline():
    scenarios = Path("tests/skill-evals/scenarios.md").read_text(encoding="utf-8")
    evaluation = Path("tests/skill-evals/with-skill.md").read_text(encoding="utf-8")
    evidence = f"{scenarios}\n{evaluation}"

    assert "`58 x 58`: 1788 beads; facial detail was flattened." in evidence
    assert (
        "`87 x 87`: 3970 beads; still less similar than the 2875-bead reference."
        in evidence
    )
    assert (
        "`110 x 122`: 10044 beads; display pixels were over-sampled as beads."
        in evidence
    )
    assert "not an exact `68 x 60` grid" in evidence
    assert "practical bead-count band" in evidence


def test_skill_owns_internal_execution_and_delivery():
    skill = Path(
        "plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md"
    ).read_text(encoding="utf-8")
    metadata = Path(
        "plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/agents/openai.yaml"
    ).read_text(encoding="utf-8")

    assert "Do not ask the user to run commands" in skill
    assert "Run the bundled compiler yourself" in skill
    assert "Host capability or permission is not installation approval." in skill
    assert "Request approval before installing a missing runtime dependency." in skill
    assert "After approval, install it internally" in skill
    assert "deliver its generated files" in skill
    assert "attached image" in metadata
    assert "$create-fuse-bead-patterns" not in metadata


def test_skill_contract_is_pattern_first_and_source_routed():
    skill_path = Path(
        "plugins/fuse-bead-designer/skills/create-fuse-bead-patterns"
    )
    skill = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    routing = (skill_path / "references/input-routing.md").read_text(encoding="utf-8")
    contract = f"{skill}\n{routing}"

    assert "Fix pattern dimensions before deriving board layout." in contract
    assert "semantic pattern draft" in contract
    assert "image generation or editing" in contract
    assert "Never ask an image model to generate counts or the final legend." in contract
    assert "Verify the actual logical grid" in contract
    assert "fail on ambiguous grid recovery" in contract
    assert "display pixels as beads" in contract
    assert "singleton cleanup is disabled by default" in contract
    for source_class in (
        "finished-bead-photo",
        "pixel-art",
        "high-resolution-image",
        "pattern-draft",
    ):
        assert source_class in routing


def test_skill_links_pattern_draft_contract_and_final_comparison():
    skill_path = Path(
        "plugins/fuse-bead-designer/skills/create-fuse-bead-patterns"
    )
    skill = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    output = (skill_path / "references/output-format.md").read_text(encoding="utf-8")
    draft_contract = skill_path / "references/pattern-draft-contract.md"

    assert draft_contract.is_file()
    assert "[pattern-draft-contract.md](references/pattern-draft-contract.md)" in skill
    assert "compare the compiled template with the source and pattern draft" in output
    assert "board layout was derived after the logical grid was fixed" in output


def test_documented_example_outputs_agree():
    for path in Path("examples/outputs").glob("*/pattern.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["total_beads"] == sum(data["color_counts"].values())


def test_public_gallery_has_four_real_compiler_examples():
    examples = (
        "occluded-finished-beads",
        "occluded-high-resolution-image",
        "actual-object-photo",
        "high-resolution-mascot",
    )
    for name in examples:
        assert Path(f"examples/inputs/{name}.png").is_file()
        output = Path("examples/outputs") / name
        for artifact in ("pattern.json", "template.png", "colors.csv", "report.json"):
            assert (output / artifact).is_file()


def test_gallery_counts_are_compiler_consistent():
    for name in ("occluded-high-resolution-image", "actual-object-photo"):
        output = Path("examples/outputs") / name
        pattern = json.loads((output / "pattern.json").read_text(encoding="utf-8"))
        assert pattern["total_beads"] == sum(pattern["color_counts"].values())


def test_verified_object_cutout_preserves_source_pixels_and_white_details():
    with Image.open("examples/inputs/actual-object-photo.png") as opened:
        source = opened.convert("RGB")
    with Image.open("examples/intermediates/actual-object-photo-clean.png") as opened:
        cutout = opened.convert("RGBA")

    alpha = cutout.getchannel("A")
    assert cutout.size == source.size
    assert alpha.getbbox() is not None

    empty = Image.new("RGB", source.size)
    source_subject = Image.composite(source, empty, alpha)
    cutout_subject = Image.composite(cutout.convert("RGB"), empty, alpha)
    assert ImageChops.difference(source_subject, cutout_subject).getbbox() is None

    output = Path("examples/outputs/actual-object-photo")
    pattern = json.loads((output / "pattern.json").read_text(encoding="utf-8"))
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert pattern["color_counts"]["warm-white"] > 0
    assert report["verification"] == "verified"


def test_packager_uses_release_version():
    packager = Path("tools/package_release.py").read_text(encoding="utf-8")
    assert 'VERSION = "0.2.0"' in packager
