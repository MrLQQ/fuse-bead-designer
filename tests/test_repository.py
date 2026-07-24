import json
from pathlib import Path


def test_chinese_readme_is_primary():
    chinese = Path("README.md").read_text(encoding="utf-8")
    english = Path("README.en.md").read_text(encoding="utf-8")

    assert "[English](README.en.md)" in chinese
    assert "[中文](README.md)" in english
    assert "安装" in chinese


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


def test_documented_example_outputs_agree():
    for path in Path("examples/outputs").glob("*/pattern.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["total_beads"] == sum(data["color_counts"].values())
