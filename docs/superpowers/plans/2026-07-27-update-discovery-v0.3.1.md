# Fuse Bead Designer v0.3.1 Update Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `v0.3.1` with a non-blocking 24-hour stable-release check and a separate, confirmation-gated update Skill.

**Architecture:** A standard-library Python checker reads a packaged policy, compares the installed version with exact stable GitHub tags, and caches every attempt for 24 hours. The existing pattern Skill only surfaces `update-available`; a new update Skill owns the host-specific, rollback-aware update transaction after explicit user confirmation.

**Tech Stack:** Python 3.10 standard library, pytest, Codex Plugin/Agent Skill Markdown, JSON manifests, deterministic ZIP packaging.

## Global Constraints

- Preserve immutable stable-tag installation; never track `main` by default.
- Check at Skill startup, but perform network access at most once per device every `86400` seconds unless the user explicitly forces a check.
- Accept only exact `vMAJOR.MINOR.PATCH` tags and compare their numeric components.
- Update discovery is read-only and must never invoke an installer or modify Plugin configuration.
- Network, cache, JSON, timeout, and rate-limit failures must not block pattern generation or emit a traceback.
- Only `update-available` produces a user notice, localized to the conversation language.
- Installation starts only after an explicit target-version confirmation.
- Never run examples, create a virtual environment, install pattern dependencies, update another Plugin, or bypass host safety approval during an update.
- After updating, verify the installed version mechanically and require a new task.
- The release version is exactly `0.3.1`.

---

### Task 1: Standard-library update policy and checker

**Files:**
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/update-policy.json`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/check_update.py`
- Create: `tests/test_update_check.py`

**Interfaces:**
- Consumes: packaged repository/version/interval metadata from `update-policy.json`.
- Produces:
  - `UpdatePolicy(repository: str, current_version: str, stable_tag_pattern: str, check_interval_seconds: int)`
  - `parse_stable_tag(tag: str) -> tuple[int, int, int] | None`
  - `select_latest_stable(tags: Iterable[str]) -> str | None`
  - `default_cache_file(system: str | None = None, environ: Mapping[str, str] | None = None, home: Path | None = None) -> Path`
  - `fetch_github_tags(repository: str, timeout: float) -> list[str]`
  - `check_for_update(policy: UpdatePolicy, cache_file: Path, *, now: int, force: bool = False, fetcher: Callable[[str, float], list[str]] = fetch_github_tags, timeout: float = 2.0) -> dict[str, object]`
  - CLI JSON with `status`, `current_version`, `latest_version`, and `checked_at`; `update-available` also contains `confirmation_prompt_zh` and `confirmation_prompt_en`.

- [ ] **Step 1: Write the failing SemVer and policy tests**

```python
import importlib.util
import json
from pathlib import Path
import sys


SCRIPT = Path(
    "plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/"
    "scripts/check_update.py"
)
POLICY = SCRIPT.parent.parent / "update-policy.json"
spec = importlib.util.spec_from_file_location("fuse_bead_update_check", SCRIPT)
update_check = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = update_check
spec.loader.exec_module(update_check)
POLICY_OBJECT = update_check.UpdatePolicy(
    repository="MrLQQ/fuse-bead-designer",
    current_version="0.3.1",
    stable_tag_pattern="vMAJOR.MINOR.PATCH",
    check_interval_seconds=86400,
)


def test_select_latest_stable_is_numeric_and_ignores_non_stable_tags():
    assert update_check.select_latest_stable(
        ["v0.9.9", "v0.10.0", "v0.11.0-rc.1", "latest", "v1.0"]
    ) == "v0.10.0"


def test_packaged_policy_is_v031():
    policy = update_check.load_policy(POLICY)
    assert policy.repository == "MrLQQ/fuse-bead-designer"
    assert policy.current_version == "0.3.1"
    assert policy.stable_tag_pattern == "vMAJOR.MINOR.PATCH"
    assert policy.check_interval_seconds == 86400
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python -m pytest \
  tests/test_update_check.py::test_select_latest_stable_is_numeric_and_ignores_non_stable_tags \
  tests/test_update_check.py::test_packaged_policy_is_v031 -q
```

Expected: collection/import failure because `check_update.py` and the policy do not exist.

- [ ] **Step 3: Implement policy loading and exact stable-tag comparison**

`update-policy.json`:

```json
{
  "repository": "MrLQQ/fuse-bead-designer",
  "current_version": "0.3.1",
  "stable_tag_pattern": "vMAJOR.MINOR.PATCH",
  "check_interval_seconds": 86400
}
```

Core parsing contract:

```python
STABLE_TAG = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def parse_stable_tag(tag: str) -> tuple[int, int, int] | None:
    match = STABLE_TAG.fullmatch(tag)
    return tuple(map(int, match.groups())) if match else None
```

- [ ] **Step 4: Run the SemVer tests and verify GREEN**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python -m pytest tests/test_update_check.py -q
```

Expected: the initial SemVer and policy tests pass.

- [ ] **Step 5: Add failing cache, network, and result-state tests**

Cover these exact behaviors with injected `fetcher` callables and a temporary
`--cache-file`:

```python
def test_recent_cache_skips_fetch(tmp_path):
    cache = tmp_path / "update.json"
    cache.write_text(
        json.dumps(
            {
                "checked_at": 100,
                "current_version": "0.3.1",
                "latest_version": "v0.3.1",
                "status": "up-to-date",
            }
        ),
        encoding="utf-8",
    )
    calls = []
    result = update_check.check_for_update(
        POLICY_OBJECT,
        cache,
        now=100 + 86399,
        fetcher=lambda repository, timeout: calls.append(repository),
    )
    assert result["status"] == "recent"
    assert calls == []


def test_newer_stable_tag_returns_localized_confirmation(tmp_path):
    result = update_check.check_for_update(
        POLICY_OBJECT,
        tmp_path / "update.json",
        now=200,
        fetcher=lambda repository, timeout: ["v0.3.1", "v0.4.0"],
    )
    assert result["status"] == "update-available"
    assert result["latest_version"] == "v0.4.0"
    assert result["confirmation_prompt_zh"] == "确认更新到 v0.4.0"


@pytest.mark.parametrize("failure", [TimeoutError(), OSError("offline"), ValueError("bad json")])
def test_expected_failures_are_unavailable_and_cached(tmp_path, failure):
    def fail(repository, timeout):
        raise failure

    result = update_check.check_for_update(
        POLICY_OBJECT, tmp_path / "update.json", now=300, fetcher=fail
    )
    assert result["status"] == "unavailable"
    assert set(json.loads((tmp_path / "update.json").read_text())) <= {
        "checked_at", "current_version", "latest_version", "status"
    }
```

Also cover:

- exact `86400` boundary performs a new fetch;
- `force=True` bypasses a recent cache;
- up-to-date behavior;
- malformed and rate-limited GitHub responses;
- unwritable cache returns `unavailable`;
- macOS, Linux/XDG, and Windows cache locations;
- expected CLI failures print one JSON object and no traceback; and
- neither the module nor tests import or call `subprocess`.

- [ ] **Step 6: Verify the expanded tests fail for missing behavior**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python -m pytest tests/test_update_check.py -q
```

Expected: failures for unimplemented cache, fetch, error, and CLI behavior.

- [ ] **Step 7: Implement the checker and CLI**

Implementation requirements:

```python
def check_for_update(...):
    cached = read_cache(cache_file)
    if not force and cached and now - int(cached["checked_at"]) < policy.check_interval_seconds:
        return recent_result(policy, cached, now)
    try:
        tags = fetcher(policy.repository, timeout)
        latest = select_latest_stable(tags)
        result = compare_result(policy, latest, now)
    except (OSError, TimeoutError, ValueError, json.JSONDecodeError):
        result = unavailable_result(policy, now)
    return persist_or_unavailable(cache_file, result)
```

Use `urllib.request.Request` with a fixed user agent, decode only the tag-name
array, write cache through a same-directory temporary file plus `Path.replace`,
and keep all cache fields on the allow-list from the tests.

CLI options:

```text
--policy PATH
--cache-file PATH
--force
--timeout SECONDS
```

- [ ] **Step 8: Run focused and repository tests**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python -m pytest \
  tests/test_update_check.py tests/test_repository.py -q
```

Expected: all focused tests pass.

- [ ] **Step 9: Commit the checker**

```bash
git add \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/update-policy.json \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/check_update.py \
  tests/test_update_check.py
git commit -m "feat: add non-blocking update discovery"
```

---

### Task 2: Pattern integration and confirmation-gated update Skill

**Files:**
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/update-discovery.md`
- Create: `plugins/fuse-bead-designer/skills/update-fuse-bead-designer/SKILL.md`
- Create: `plugins/fuse-bead-designer/skills/update-fuse-bead-designer/agents/openai.yaml`
- Modify: `tests/test_repository.py`

**Interfaces:**
- Consumes: Task 1 CLI statuses and confirmation prompts.
- Produces:
  - pattern-start behavior that never blocks compilation;
  - `update-fuse-bead-designer` trigger for checking, confirming, and updating this Plugin;
  - rollback-aware Codex transaction and host-native fallback guidance.

- [ ] **Step 1: Add failing Skill contract tests**

Add assertions equivalent to:

```python
from pathlib import Path


CREATE_SKILL = Path(
    "plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md"
)
UPDATE_SKILL = Path(
    "plugins/fuse-bead-designer/skills/update-fuse-bead-designer/SKILL.md"
)


def test_pattern_skill_checks_updates_without_blocking_generation():
    skill = CREATE_SKILL.read_text()
    assert "scripts/check_update.py" in skill
    assert "Do not use `--force` during ordinary pattern generation." in skill
    assert "Only surface `update-available`" in skill
    assert "continue the pattern task" in skill


def test_update_skill_requires_confirmation_verification_and_rollback():
    skill = UPDATE_SKILL.read_text()
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
```

Assert the update reference explains the four statuses, 24-hour behavior,
standalone-host boundary, and the rule that host permission prompts are not
bypassed.

- [ ] **Step 2: Run contract tests and verify RED**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python -m pytest \
  tests/test_repository.py::test_pattern_skill_checks_updates_without_blocking_generation \
  tests/test_repository.py::test_update_skill_requires_confirmation_verification_and_rollback -q
```

Expected: failures because the integration and update Skill do not exist.

- [ ] **Step 3: Add the non-blocking pattern startup step**

Add an early Skill step that tells the Agent to execute:

```bash
python scripts/check_update.py
```

The instruction must retain an `update-available` notice for the final response,
discard all other statuses, never use `--force` during ordinary generation,
and continue even when the command cannot run.

- [ ] **Step 4: Create the update reference and dedicated Skill**

The new Skill frontmatter is:

```yaml
---
name: update-fuse-bead-designer
description: Check or update the Fuse Bead Designer Plugin or standalone Skill. Use when the user asks whether this specific Plugin has an update, asks to update it, or confirms a version-specific notice such as “确认更新到 v0.4.0”.
---
```

The Skill must:

1. run the checker with `--force`;
2. validate the requested target against the fresh latest stable tag;
3. require the explicit versioned confirmation before writes;
4. inspect only the named Marketplace and Plugin;
5. prefer the host's Plugin manager;
6. on Codex, record the old stable ref, rebind to the target ref, reinstall,
   and read `codex plugin list --json`;
7. restore the old stable ref if target verification fails; and
8. stop after success and request a new task.

Generate `agents/openai.yaml` with:

```yaml
interface:
  display_name: "Update Fuse Bead Designer"
  short_description: "Safely check and update the plugin"
  default_prompt: "Check Fuse Bead Designer for a stable update and update it only after I confirm the exact version."
```

- [ ] **Step 5: Validate both Skills and run repository tests**

Run:

```bash
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/update-fuse-bead-designer
../v0.3-pattern-architecture/.venv/bin/python -m pytest \
  tests/test_update_check.py tests/test_repository.py -q
```

Expected: both validators and all focused tests pass.

- [ ] **Step 6: Commit Skill integration**

```bash
git add \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/update-discovery.md \
  plugins/fuse-bead-designer/skills/update-fuse-bead-designer \
  tests/test_repository.py
git commit -m "feat: add confirmation-gated plugin updates"
```

---

### Task 3: v0.3.1 documentation and synchronized release metadata

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `AGENTS.md`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `plugins/fuse-bead-designer/.codex-plugin/plugin.json`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/update-policy.json`
- Modify: `pyproject.toml`
- Modify: `tools/package_release.py`
- Modify: `tests/test_repository.py`
- Modify: `tests/skill-evals/with-skill.md`

**Interfaces:**
- Consumes: checker and update Skill behavior from Tasks 1–2.
- Produces: Chinese-first natural-language update documentation and one
  synchronized `0.3.1` release identity.

- [ ] **Step 1: Add failing README and version-sync assertions**

Require:

```python
assert "## 自动发现更新：一句话确认" in chinese
assert "确认更新到 v0.4.0" in chinese
assert "24 小时内最多检查一次" in chinese
assert "不会阻塞拼豆图生成" in chinese
assert "## Automatic update discovery" in english
```

Update version synchronization to require `0.3.1` in:

- Plugin manifest;
- Marketplace manifest;
- `pyproject.toml`;
- packager;
- update policy;
- both README files; and
- `AGENTS.md`.

The `AGENTS.md` test must distinguish installation, read-only update checking,
and a version-confirmed update as three separate intents.

- [ ] **Step 2: Run repository tests and verify RED**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python -m pytest tests/test_repository.py -q
```

Expected: README/update-contract and version-sync failures.

- [ ] **Step 3: Update Chinese-first documentation**

Place the update section after daily natural-language usage and before the
pattern architecture. The user-facing prompt is:

> 请检查 Fuse Bead Designer 是否有新版本；如果发现新版，告诉我版本号，不要自动安装。

Document the automatic notice and the exact confirmation reply. State that the
Agent owns all internal commands, that the host may still request safety
approval, and that a new task is required after success.

In the developer section, explain why a pinned tag does not advance when a Git
Marketplace is merely refreshed.

- [ ] **Step 4: Update `AGENTS.md` and all version sources**

The update contract must explicitly prohibit treating “install”, “check”, and
“update” as interchangeable authorizations. Bump every version source to
`0.3.1`, including the default installation ref `v0.3.1`.

- [ ] **Step 5: Update the forward-eval rubric**

Add scenarios for:

- ordinary pattern generation with no update;
- an available update notice that does not interrupt delivery;
- offline checking;
- an unconfirmed update request; and
- a confirmed exact stable version update.

- [ ] **Step 6: Run focused tests and validators**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python -m pytest \
  tests/test_update_check.py tests/test_repository.py -q
python3 /Users/bytedance/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/fuse-bead-designer
```

Expected: all focused tests and Plugin validation pass.

- [ ] **Step 7: Commit documentation and release metadata**

```bash
git add \
  README.md README.en.md AGENTS.md .agents/plugins/marketplace.json \
  plugins/fuse-bead-designer/.codex-plugin/plugin.json \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/update-policy.json \
  pyproject.toml tools/package_release.py tests/test_repository.py \
  tests/skill-evals/with-skill.md
git commit -m "docs: document one-sentence plugin updates"
```

---

### Task 4: Complete verification, deterministic packaging, and publication

**Files:**
- Generate once: `dist/fuse-bead-designer-plugin-v0.3.1.zip`
- Generate once: `dist/create-fuse-bead-patterns-skill-v0.3.1.zip`
- Inspect: all committed changes from `v0.3.0..HEAD`

**Interfaces:**
- Consumes: reviewed code, Skills, docs, tests, and synchronized release data.
- Produces: verified `v0.3.1` archives, `main` commit, and immutable Git tag.

- [ ] **Step 1: Run the full fresh verification**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python -m pytest -q
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/update-fuse-bead-designer
python3 /Users/bytedance/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/fuse-bead-designer
git diff --check
```

Expected: every command passes.

- [ ] **Step 2: Build the two release archives exactly once**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python tools/package_release.py
```

Do not rerun the packager unless a subsequent code or packaged-document change
makes these archives obsolete.

- [ ] **Step 3: Inspect archive roots, versions, files, privacy, and hashes**

Use `zipfile` to assert:

- Plugin root is `fuse-bead-designer/`;
- standalone root is `create-fuse-bead-patterns/`;
- Plugin manifest, Marketplace data, and update policy contain `0.3.1`;
- the Plugin archive contains both Skills;
- the standalone archive contains the checker, policy, and update reference;
- neither archive contains cache JSON, `.git`, `.venv`, private absolute paths,
  credentials, or tokens; and
- both SHA-256 values are reported.

- [ ] **Step 4: Review the complete release diff**

Inspect:

```bash
git status --short --branch
git diff --stat v0.3.0..HEAD
git diff --check v0.3.0..HEAD
```

Resolve any Critical or Important correctness, security, installer, or
documentation mismatch, then repeat Step 1. Rebuild only if packaged content
changed.

- [ ] **Step 5: Fast-forward `main`, tag, and push**

From the primary checkout:

```bash
git merge --ff-only agent/v0.3.1-update-discovery
git tag -a v0.3.1 -m "Fuse Bead Designer v0.3.1"
git push origin main v0.3.1
```

Verify:

```bash
git ls-remote origin refs/heads/main refs/tags/v0.3.1 refs/tags/v0.3.1^{}
```

Expected: `main` and the peeled annotated tag resolve to the reviewed release
commit.
