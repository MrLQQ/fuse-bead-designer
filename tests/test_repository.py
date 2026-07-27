import csv
import json
from pathlib import Path

from PIL import Image, ImageChops


CREATE_SKILL = Path(
    "plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md"
)
UPDATE_SKILL = Path(
    "plugins/fuse-bead-designer/skills/update-fuse-bead-designer/SKILL.md"
)
UPDATE_REFERENCE = Path(
    "plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/"
    "references/update-discovery.md"
)


def test_pattern_skill_checks_updates_without_blocking_generation():
    skill = CREATE_SKILL.read_text(encoding="utf-8")

    assert "scripts/check_update.py" in skill
    assert "Do not use `--force` during ordinary pattern generation." in skill
    assert "Only surface `update-available`" in skill
    assert "continue the pattern task" in skill


def test_update_skill_requires_confirmation_verification_and_rollback():
    skill = UPDATE_SKILL.read_text(encoding="utf-8")

    for phrase in (
        "确认更新到 v",
        "exact stable tag",
        "record the installed version",
        "restore the previous stable tag",
        "verify the installed version",
        "start a new task",
    ):
        assert phrase in skill
    for forbidden in ("track `main`", "run examples", "create a virtual environment"):
        assert forbidden in skill


def test_update_reference_defines_statuses_interval_and_host_boundary():
    reference = UPDATE_REFERENCE.read_text(encoding="utf-8")

    for status in ("recent", "up-to-date", "update-available", "unavailable"):
        assert status in reference
    assert "24-hour" in reference
    assert "standalone" in reference
    assert "Do not bypass host permission prompts." in reference


def test_chinese_readme_is_primary():
    chinese = Path("README.md").read_text(encoding="utf-8")
    english = Path("README.en.md").read_text(encoding="utf-8")

    assert "[English](README.en.md)" in chinese
    assert "[中文](README.md)" in english
    assert "安装" in chinese


def test_readmes_put_natural_language_before_developer_cli():
    chinese = Path("README.md").read_text(encoding="utf-8")
    english = Path("README.en.md").read_text(encoding="utf-8")

    assert (
        "请安装这个 Codex 插件：https://github.com/MrLQQ/fuse-bead-designer "
        "。请由你完成安装；安装成功后停止，不要运行示例或安装额外运行依赖，"
        "只提醒我新建任务。"
    ) in chinese
    assert "把这张图生成拼豆设计图。" in chinese
    assert chinese.index("## 开发者") < chinese.index("python ")

    assert "Please install this Codex plugin: https://github.com/MrLQQ/fuse-bead-designer" in english
    assert "Turn the attached image into a fuse-bead pattern" in english
    assert english.index("## Developer") < english.index("python ")


def test_v03_readmes_define_the_pattern_first_contract():
    chinese = Path("README.md").read_text(encoding="utf-8")
    english = Path("README.en.md").read_text(encoding="utf-8")

    assert "## v0.3.0 图案优先流程" in chinese
    assert "v0.3.0 把“理解图片”和“生成可计数图纸”明确分开" in chinese
    assert "## The v0.3.0 pattern-first flow" in english
    assert "v0.3.0 deliberately separates understanding an image" in english

    for phrase in (
        "三条输入路线",
        "拼豆成品照",
        "像素画或现成图纸",
        "普通照片或高清插画",
        "语义图案草稿",
        "先确定图案尺寸，再推导拼板布局",
        "任意正整数宽高",
        "确定性统计",
        "推断区域",
        "校正后的规则网格",
        "不会自动检测普通照片中的通用拼豆晶格",
    ):
        assert phrase in chinese

    for phrase in (
        "three input routes",
        "finished-bead photo",
        "pixel art or an existing pattern",
        "ordinary photo or high-resolution illustration",
        "semantic pattern draft",
        "fix the pattern dimensions before deriving the board layout",
        "arbitrary positive integer width and height",
        "deterministic counts",
        "inferred regions",
        "rectified regular grid",
        "does not automatically detect a general bead lattice in ordinary photos",
    ):
        assert phrase in english.lower()


def test_readmes_document_runnable_finished_bead_route_and_conditional_review():
    chinese = Path("README.md").read_text(encoding="utf-8")
    english = Path("README.en.md").read_text(encoding="utf-8")

    for readme in (chinese, english):
        assert (
            "--input "
            "examples/intermediates/occluded-finished-beads-pattern-draft.png"
        ) in readme
        assert "--classification finished-bead-photo \\\n  --rectified-grid" in readme
        assert "--width 58 --height 58" in readme
        assert "occluded-finished-beads-clean.png" not in readme

    assert "只有 `report.json` 记录了 `inferred_cells` 或 `cleanup_changes` 时" in chinese
    assert "对照原始素材与语义图案草稿" in chinese
    assert "only when `report.json` lists `inferred_cells` or `cleanup_changes`" in english
    assert "compare the source with the semantic pattern draft" in english


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
    marketplace = json.loads(
        Path(".agents/plugins/marketplace.json").read_text(encoding="utf-8")
    )
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    packager = Path("tools/package_release.py").read_text(encoding="utf-8")
    chinese = Path("README.md").read_text(encoding="utf-8")
    english = Path("README.en.md").read_text(encoding="utf-8")
    agents = Path("AGENTS.md").read_text(encoding="utf-8")

    assert plugin["version"] == "0.3.0"
    assert marketplace["version"] == "0.3.0"
    assert 'version = "0.3.0"' in pyproject
    assert 'VERSION = "0.3.0"' in packager
    for text in (chinese, english, agents):
        assert "v0.3.0" in text
        assert "v0.2.0" not in text


def test_agents_installation_contract_is_agent_owned():
    contract = Path("AGENTS.md").read_text(encoding="utf-8")

    assert "Request permission before installing anything." in contract
    assert "check whether the `fuse-bead-designer` Marketplace is already installed" in contract
    assert "Then separately check whether the `fuse-bead-designer` plugin is installed" in contract
    assert "If the Marketplace is not installed, run this command internally:" in contract
    assert "codex plugin marketplace add MrLQQ/fuse-bead-designer --ref v0.3.0" in contract
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


def test_skill_high_resolution_command_preserves_original_and_draft_provenance():
    skill_path = Path("plugins/fuse-bead-designer/skills/create-fuse-bead-patterns")
    skill = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    routing = (skill_path / "references/input-routing.md").read_text(encoding="utf-8")
    output = (skill_path / "references/output-format.md").read_text(encoding="utf-8")
    assert "<!-- high-resolution-command:start -->" in skill
    assert "<!-- high-resolution-command:end -->" in skill
    high_resolution_command = skill.split(
        "<!-- high-resolution-command:start -->", 1
    )[1].split("<!-- high-resolution-command:end -->", 1)[0]

    assert "--input <original-source.png>" in high_resolution_command
    assert "--classification high-resolution-image" in high_resolution_command
    assert "--draft-input <semantic-pattern-draft.png>" in high_resolution_command
    assert "--width <verified-logical-columns>" in high_resolution_command
    assert "--height <verified-logical-rows>" in high_resolution_command
    assert "--grid-box <left,top,right,bottom>" in high_resolution_command
    assert "--verification <inferred-low|review-required>" in high_resolution_command
    assert "Do not use the generic pattern-draft command" in high_resolution_command
    assert "counts or the final legend" in high_resolution_command
    for contract in (skill, routing, output):
        assert "high-resolution-image" in contract
        assert "cannot use `verified`" in contract


def test_documented_example_outputs_agree():
    for path in Path("examples/outputs").glob("*/pattern.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        output = path.parent
        with (output / "colors.csv").open(encoding="utf-8", newline="") as stream:
            csv_counts = {
                row["id"]: int(row["count"])
                for row in csv.DictReader(stream)
                if int(row["count"])
            }

        assert data["total_beads"] == sum(data["color_counts"].values())
        assert csv_counts == data["color_counts"]
        for artifact in ("template.png", "report.json"):
            assert (output / artifact).is_file()


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


def test_public_examples_use_exact_v03_source_routes():
    route_expectations = {
        "clean-pixel-art": {
            "classification": "pixel-art",
            "source_input": "examples/inputs/clean-pixel-art.png",
            "compiled_input": "examples/inputs/clean-pixel-art.png",
            "draft_input": None,
            "width": 16,
            "height": 16,
            "verification": "verified",
        },
        "occluded-finished-beads": {
            "classification": "finished-bead-photo",
            "source_input": (
                "examples/intermediates/occluded-finished-beads-pattern-draft.png"
            ),
            "compiled_input": (
                "examples/intermediates/occluded-finished-beads-pattern-draft.png"
            ),
            "draft_input": None,
            "width": 58,
            "height": 58,
            "verification": "review-required",
        },
        "occluded-high-resolution-image": {
            "classification": "high-resolution-image",
            "source_input": "examples/inputs/occluded-high-resolution-image.png",
            "compiled_input": (
                "examples/intermediates/"
                "occluded-high-resolution-image-pattern-draft.png"
            ),
            "draft_input": (
                "examples/intermediates/"
                "occluded-high-resolution-image-pattern-draft.png"
            ),
            "width": 58,
            "height": 58,
            "verification": "review-required",
        },
        "actual-object-photo": {
            "classification": "high-resolution-image",
            "source_input": "examples/inputs/actual-object-photo.png",
            "compiled_input": (
                "examples/intermediates/actual-object-photo-pattern-draft.png"
            ),
            "draft_input": (
                "examples/intermediates/actual-object-photo-pattern-draft.png"
            ),
            "width": 58,
            "height": 29,
            "verification": "review-required",
        },
        "high-resolution-mascot": {
            "classification": "high-resolution-image",
            "source_input": "examples/inputs/high-resolution-mascot.png",
            "compiled_input": (
                "examples/intermediates/high-resolution-mascot-pattern-draft.png"
            ),
            "draft_input": (
                "examples/intermediates/high-resolution-mascot-pattern-draft.png"
            ),
            "width": 58,
            "height": 58,
            "verification": "review-required",
        },
    }

    for name, expected in route_expectations.items():
        output = Path("examples/outputs") / name
        pattern = json.loads((output / "pattern.json").read_text(encoding="utf-8"))
        report = json.loads((output / "report.json").read_text(encoding="utf-8"))
        settings = pattern["settings"]

        assert pattern["width"] == expected["width"]
        assert pattern["height"] == expected["height"]
        assert pattern["verification"] == expected["verification"]
        assert settings["grid_evidence"]["source"] == "declared"
        assert settings["source_classification"] == expected["classification"]
        assert settings["sampling"] == "center"
        assert settings["cleanup"] is False
        assert settings["source_input"] == expected["source_input"]
        assert settings["compiled_input"] == expected["compiled_input"]
        assert settings["draft_input"] == expected["draft_input"]

        assert report["classification"] == expected["classification"]
        assert report["verification"] == expected["verification"]
        assert report["source_classification"] == expected["classification"]
        assert report["grid_evidence"] == settings["grid_evidence"]
        assert report["sampling"] == "center"
        assert report["cleanup"] is False
        assert report["source_input"] == expected["source_input"]
        assert report["compiled_input"] == expected["compiled_input"]
        assert report["draft_input"] == expected["draft_input"]
        assert report["draft_used"] is (expected["draft_input"] is not None)
        assert report["cleanup_changes"] == []
        assert report["inferred_cells"] == []
        assert not (output / "review.png").exists()

        with Image.open(expected["compiled_input"]) as compiled:
            assert compiled.width >= expected["width"] * 4
            assert compiled.height >= expected["height"] * 4


def test_v03_release_archive_contract_replaces_v02():
    packager = Path("tools/package_release.py").read_text(encoding="utf-8")
    plugin = json.loads(
        Path("plugins/fuse-bead-designer/.codex-plugin/plugin.json").read_text(
            encoding="utf-8"
        )
    )

    assert "v0.2.0" not in packager
    assert 'VERSION = "0.3.0"' in packager
    assert 'f"fuse-bead-designer-plugin-v{VERSION}.zip"' in packager
    assert 'f"create-fuse-bead-patterns-skill-v{VERSION}.zip"' in packager
    assert "member = Path(source.name) / path.relative_to(source)" in packager
    assert plugin["version"] == "0.3.0"


def test_object_cutout_preserves_source_pixels_and_white_details():
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
    assert report["verification"] == "review-required"
