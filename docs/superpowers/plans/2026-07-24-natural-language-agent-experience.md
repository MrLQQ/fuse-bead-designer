# Natural-Language Agent Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make installation a one-time Agent-owned action and make every normal fuse-bead generation request use only an attached image plus natural language.

**Architecture:** Keep the Codex Plugin as the primary distribution and the standalone Agent Skill as the portable fallback. Add a repository-level Agent installation contract, give the remote marketplace a collision-safe identity, teach the Skill that CLI execution is an internal implementation detail, and move all user-visible command examples into a clearly separated developer section.

**Tech Stack:** Codex Plugin marketplace JSON, Agent Skills Markdown/YAML, Python 3.10+, pytest, deterministic ZIP packaging.

## Global Constraints

- A Plugin or Skill must never bypass host permission or installation confirmation.
- Newly installed Codex skills are picked up in a new task.
- Normal users must not be asked to execute Python or Codex CLI commands.
- The compiler remains the sole source of truth for cells and quantities.
- Chinese documentation is primary; English documentation is the fallback.
- Release version is `0.2.0`.

---

### Task 1: Agent-owned installation contract

**Files:**
- Create: `AGENTS.md`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `plugins/fuse-bead-designer/.codex-plugin/plugin.json`
- Modify: `pyproject.toml`
- Modify: `tests/test_repository.py`

**Interfaces:**
- Consumes: the existing Git marketplace layout and `fuse-bead-designer` plugin directory.
- Produces: marketplace selector `fuse-bead-designer@fuse-bead-designer`, plugin version `0.2.0`, and machine-readable installation instructions for an Agent given the repository URL.

- [ ] **Step 1: Write failing repository contract tests**

Add tests that require the remote marketplace identity, synchronized versions, and an Agent-owned installation contract:

```python
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
    assert "codex plugin marketplace add MrLQQ/fuse-bead-designer --ref v0.2.0" in contract
    assert "codex plugin add fuse-bead-designer@fuse-bead-designer" in contract
    assert "Do not ask the user to run" in contract
    assert "new task" in contract
```

- [ ] **Step 2: Run tests and verify the current repository fails**

Run:

```bash
.venv/bin/pytest tests/test_repository.py -q
```

Expected: failures for marketplace name `personal`, version `0.1.0`, and missing `AGENTS.md`.

- [ ] **Step 3: Implement the installation contract**

Create `AGENTS.md` with imperative instructions for:

- recognizing “install/use this repository” intent;
- requesting permission before installation;
- internally running the two Codex commands;
- avoiding duplicate Marketplace installation;
- using the standalone Release Skill on compatible non-Codex hosts;
- telling the user to start a new task after successful Codex installation;
- never making the user copy CLI commands.

Change the Marketplace root to:

```json
{
  "name": "fuse-bead-designer",
  "interface": {
    "displayName": "Fuse Bead Designer"
  }
}
```

Set both Plugin and Python project versions to `0.2.0`.

- [ ] **Step 4: Run the focused repository tests**

Run:

```bash
.venv/bin/pytest tests/test_repository.py -q
```

Expected: all repository tests pass.

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md .agents/plugins/marketplace.json \
  plugins/fuse-bead-designer/.codex-plugin/plugin.json pyproject.toml \
  tests/test_repository.py
git commit -m "feat: add agent-owned installation contract"
```

### Task 2: Natural-language Skill orchestration

**Files:**
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/agents/openai.yaml`
- Modify: `tests/test_repository.py`
- Modify: `tests/skill-evals/scenarios.md`

**Interfaces:**
- Consumes: the bundled `scripts/create_pattern.py` compiler and existing routing/palette/output references.
- Produces: a Skill that owns inspection, cleanup, compiler invocation, verification, and artifact delivery after a natural-language image request.

- [ ] **Step 1: Add failing Skill-behavior assertions**

Add:

```python
def test_skill_owns_internal_execution_and_delivery():
    skill = Path(
        "plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md"
    ).read_text(encoding="utf-8")
    metadata = Path(
        "plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/agents/openai.yaml"
    ).read_text(encoding="utf-8")

    assert "Do not ask the user to run commands" in skill
    assert "Run the bundled compiler yourself" in skill
    assert "attached image" in metadata
    assert "$create-fuse-bead-patterns" not in metadata
```

Add a natural-language scenario to `tests/skill-evals/scenarios.md`:

```text
把我上传的图片生成拼豆设计图。优先使用常规 29×29 拼豆板，
自动处理背景或手指遮挡，并告诉我每种颜色和数量。
```

- [ ] **Step 2: Run the focused test and verify failure**

Run:

```bash
.venv/bin/pytest tests/test_repository.py::test_skill_owns_internal_execution_and_delivery -q
```

Expected: failure because the current Skill exposes the compiler command without explicitly owning execution and its UI prompt exposes the Skill name.

- [ ] **Step 3: Rewrite the Skill contract**

Update frontmatter discovery terms to cover finished bead photos, pixel art, illustrations, high-resolution images, 拼豆图纸, 拼豆模板, 像素拼豆, color counts, and bead quantities.

At the start of the body, require the Agent to:

```text
Own the complete workflow. Do not ask the user to run commands or install
runtime dependencies when the host can do so with the available permissions.
Run the bundled compiler yourself and deliver its generated files.
```

Keep the exact compiler command in an “Internal execution” section for the Agent. Preserve all uncertainty, board, palette, and deterministic-count rules.

Change `agents/openai.yaml` to natural user-facing copy:

```yaml
interface:
  display_name: "Fuse Bead Designer"
  short_description: "Turn an attached image into a buildable bead pattern"
  default_prompt: "Turn the attached image into a buildable fuse-bead pattern and report each color quantity."
```

- [ ] **Step 4: Run focused tests and Skill validation**

Run:

```bash
.venv/bin/pytest tests/test_repository.py -q
/opt/homebrew/bin/python3 \
  /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
```

Expected: repository tests pass and validator prints `Skill is valid!`.

- [ ] **Step 5: Commit**

```bash
git add plugins/fuse-bead-designer/skills/create-fuse-bead-patterns \
  tests/test_repository.py tests/skill-evals/scenarios.md
git commit -m "feat: make bead generation natural-language first"
```

### Task 3: User-first README and developer-only CLI

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `tests/test_repository.py`

**Interfaces:**
- Consumes: the Agent installation contract and natural-language Skill behavior from Tasks 1–2.
- Produces: a Chinese-first onboarding path containing no user-run commands and a separate developer reference containing all CLI examples.

- [ ] **Step 1: Add failing README information-architecture tests**

Add:

```python
def test_readmes_put_natural_language_before_developer_cli():
    chinese = Path("README.md").read_text(encoding="utf-8")
    english = Path("README.en.md").read_text(encoding="utf-8")

    assert "请安装并使用 https://github.com/MrLQQ/fuse-bead-designer" in chinese
    assert "把这张图生成拼豆设计图" in chinese
    assert chinese.index("## 开发者") < chinese.index("python ")

    assert "Please install and use https://github.com/MrLQQ/fuse-bead-designer" in english
    assert "Turn the attached image into a fuse-bead pattern" in english
    assert english.index("## Developer") < english.index("python ")
```

- [ ] **Step 2: Run the focused README test and verify failure**

Run:

```bash
.venv/bin/pytest tests/test_repository.py::test_readmes_put_natural_language_before_developer_cli -q
```

Expected: failure because command-line installation and compiler usage currently appear in the user quick start.

- [ ] **Step 3: Rewrite both README files**

Use this order in Chinese and English:

1. value proposition and screenshot;
2. “send this to your Agent” first-install prompt;
3. “upload an image and say this” daily-use prompt;
4. delivered files and uncertainty states;
5. supported input types and board/palette behavior;
6. Codex/other-Agent installation boundary;
7. developer section containing Marketplace, Python, testing, packaging, and direct compiler commands.

Explicitly say the displayed commands are for Agent implementers/developers and normal users should not run them.

- [ ] **Step 4: Run repository tests**

Run:

```bash
.venv/bin/pytest tests/test_repository.py -q
```

Expected: all repository tests pass.

- [ ] **Step 5: Commit**

```bash
git add README.md README.en.md tests/test_repository.py
git commit -m "docs: make agent prompts the primary workflow"
```

### Task 4: v0.2.0 packaging and release readiness

**Files:**
- Modify: `tools/package_release.py`
- Modify: `tests/test_repository.py`
- Modify: `plugins/fuse-bead-designer/.codex-plugin/plugin.json` only if validation requires a manifest correction.

**Interfaces:**
- Consumes: the v0.2.0 Plugin and Skill produced by Tasks 1–3.
- Produces: deterministic `v0.2.0` Plugin and standalone Skill archives plus a release-ready branch.

- [ ] **Step 1: Add a failing package-version test**

Add:

```python
def test_packager_uses_release_version():
    packager = Path("tools/package_release.py").read_text(encoding="utf-8")
    assert 'VERSION = "0.2.0"' in packager
```

- [ ] **Step 2: Run the focused test and verify failure**

Run:

```bash
.venv/bin/pytest tests/test_repository.py::test_packager_uses_release_version -q
```

Expected: failure because the packager still uses `0.1.0`.

- [ ] **Step 3: Update the deterministic packager**

Change:

```python
VERSION = "0.2.0"
```

Do not change archive contents, timestamps, ordering, or compression policy.

- [ ] **Step 4: Run final bounded verification**

Run exactly once:

```bash
.venv/bin/pytest -q
/opt/homebrew/bin/python3 \
  /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
/opt/homebrew/bin/python3 \
  /Users/bytedance/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/fuse-bead-designer
.venv/bin/python tools/package_release.py
shasum -a 256 dist/*-v0.2.0.zip
git diff --check
```

Expected:  all tests pass; both validators pass; two v0.2.0 archives exist; SHA-256 values print; no whitespace errors.

- [ ] **Step 5: Perform one forward acceptance check**

Give a fresh Agent only the repository URL, the installation request below, and the repository files:

```text
请安装并使用 https://github.com/MrLQQ/fuse-bead-designer。
安装过程由你完成，不要让我运行命令。
```

Pass only if it identifies the Git Marketplace and Plugin selector, requests installation authority, performs the commands itself, and tells the user to start a new task. Do not run image generation or the full compiler suite again.

- [ ] **Step 6: Commit**

```bash
git add tools/package_release.py tests/test_repository.py
git commit -m "build: prepare v0.2.0 release archives"
```

- [ ] **Step 7: Publish after local verification**

Fast-forward `main`, push it to `MrLQQ/fuse-bead-designer`, create GitHub Release `v0.2.0`, and attach:

```text
dist/fuse-bead-designer-plugin-v0.2.0.zip
dist/create-fuse-bead-patterns-skill-v0.2.0.zip
```

Verify that both assets and commit SHA are visible on the release page.
