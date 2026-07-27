# Semantic Multi-Size Patterns Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release Fuse Bead Designer `v0.4.0` with baseline-first delivery and optional semantic economy, balanced, and detail variants that never use mechanical downsampling as the final design method.

**Architecture:** Keep image understanding and semantic redraw in the Agent Skill, while deterministic Python owns advisory target sizes and validates/aggregates independently compiled variant artifacts. A shared feature contract describes the current image rather than assuming a human subject. The existing compiler remains the sole source of bead counts.

**Tech Stack:** Python 3.10+, Pillow, JSON, CSV, pytest, Markdown Agent Skills.

## Global Constraints

- Default requests deliver one baseline pattern, then offer optional multi-size variants.
- Explicit multi-size, budget, or board-comparison requests generate variants immediately.
- Every task-specific hard semantic feature must survive; image content is not assumed to be a person.
- Fixed-ratio, average, median, or generic low-resolution downsampling must not produce a final variant.
- Each tier has at most two semantic candidates: one initial candidate and one larger retry.
- Cancel a failing tier and merge materially duplicate adjacent tiers; output may contain two to four accepted versions.
- Pattern dimensions are fixed before 29 x 29 board layout is derived.
- Only compiler artifacts own cells, quantities, and board layout.
- Semantic redesigns use `review-required`; only an unchanged mechanically verified baseline may use `verified`.
- Release version is exactly `0.4.0`.

---

### Task 1: Advisory semantic size planner

**Files:**
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/sizing.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/__init__.py`
- Modify: `tests/test_sizing.py`

**Interfaces:**
- Preserves: `PatternSizeCandidate` and `recommend_pattern_sizes(...)` for compatibility.
- Produces:
  - `SemanticSizeTarget(name: str, width: int, height: int, target_long_side: int, attempt: int)`
  - `plan_semantic_size_targets(baseline_width: int, baseline_height: int, minimum_long_side: int) -> tuple[SemanticSizeTarget, ...]`
  - `expand_semantic_size_target(target: SemanticSizeTarget, baseline_width: int, baseline_height: int) -> SemanticSizeTarget | None`

- [ ] **Step 1: Write failing planner tests**

Add tests with hand-derived expectations:

```python
def test_semantic_targets_span_minimum_to_baseline_without_board_multiples():
    targets = plan_semantic_size_targets(132, 144, 63)
    assert [target.name for target in targets] == ["economy", "balanced", "detail"]
    assert [target.target_long_side for target in targets] == [63, 104, 128]
    assert all(target.width < 132 and target.height < 144 for target in targets)
    assert any(target.width % 29 or target.height % 29 for target in targets)


def test_semantic_targets_deduplicate_when_the_feasible_span_is_small():
    targets = plan_semantic_size_targets(20, 21, 18)
    assert len({(target.width, target.height) for target in targets}) == len(targets)
    assert len(targets) < 3


def test_semantic_retry_expands_once_but_never_reaches_past_baseline():
    target = plan_semantic_size_targets(132, 144, 63)[0]
    retry = expand_semantic_size_target(target, 132, 144)
    assert retry is not None
    assert retry.attempt == 2
    assert retry.target_long_side > target.target_long_side
    assert expand_semantic_size_target(retry, 132, 144) is None
```

Also reject Boolean, non-integer, non-positive, and `minimum_long_side >= baseline_long_side` inputs.

- [ ] **Step 2: Verify RED**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python -m pytest tests/test_sizing.py -q
```

Expected: import failures for the new planner API.

- [ ] **Step 3: Implement the planner**

Use aspect-preserving half-up integer rounding. The three initial long-side targets are:

```python
minimum
round(minimum + (baseline - minimum) * 0.50)
round(minimum + (baseline - minimum) * 0.80)
```

Discard duplicate targets and any target that reaches the baseline. A retry grows the current long side by `max(2, ceil(current * 0.10))`, remains below the baseline, and is allowed only when `attempt == 1`.

- [ ] **Step 4: Verify GREEN and commit**

Run the focused test once, then:

```bash
git add \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/sizing.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/__init__.py \
  tests/test_sizing.py
git commit -m "feat: plan semantic size variants"
```

---

### Task 2: Deterministic variant-set validator and comparison builder

**Files:**
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/variant_set.py`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/build_variant_set.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/__init__.py`
- Create: `tests/test_variant_set.py`

**Interfaces:**
- Consumes a root containing `feature-contract.json` and two to four accepted variant directories.
- Each variant contains `manifest.json` plus compiler-created `artifacts/pattern.json`, `colors.csv`, `template.png`, and `review.png`.
- Produces:
  - `validate_feature_contract(data: object) -> dict[str, object]`
  - `validate_variant_set(root: Path) -> dict[str, object]`
  - `render_variant_comparison(summary: dict[str, object], destination: Path) -> None`
  - CLI-created `summary.json` and `comparison.png`.

- [ ] **Step 1: Write failing behavior tests**

Use temporary two-pixel fixtures and literal JSON/CSV data. Cover:

```python
def test_variant_set_accepts_two_to_four_compiled_semantic_versions(tmp_path):
    root = build_valid_variant_fixture(tmp_path, names=("economy", "baseline"))
    summary = validate_variant_set(root)
    assert [item["name"] for item in summary["variants"]] == ["economy", "baseline"]
    assert summary["recommended"] == "economy"


def test_variant_set_rejects_an_accepted_variant_missing_a_hard_feature(tmp_path):
    root = build_valid_variant_fixture(tmp_path, names=("economy", "baseline"))
    set_feature_result(root / "economy" / "manifest.json", "handle", False)
    with pytest.raises(ValueError, match="hard feature handle failed"):
        validate_variant_set(root)


def test_variant_set_rejects_more_than_two_attempts_and_duplicate_tiers(tmp_path):
    ...


def test_variant_set_recounts_pattern_and_csv_instead_of_trusting_manifest(tmp_path):
    ...
```

Also cover:

- a generic feature contract for a non-human object;
- unique feature IDs and `hard|soft` importance;
- positive dimensions;
- non-baseline accepted variants must be `review-required`;
- manifest dimensions and totals match compiler artifacts;
- board columns/rows equal `ceil(width/29)` and `ceil(height/29)`;
- accepted variants increase in long-side size and bead count;
- unreadable PNGs fail;
- comparison and summary files are produced.

- [ ] **Step 2: Verify RED**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python -m pytest tests/test_variant_set.py -q
```

Expected: import failure because `variant_set.py` does not exist.

- [ ] **Step 3: Implement validation**

Use only standard-library JSON/CSV validation plus Pillow for PNG verification and comparison rendering. Do not claim that code can visually decide whether a feature is truly present; it verifies that every Agent-reviewed hard feature has an explicit passing result and that all deterministic compiler data agree.

Required accepted manifest fields:

```json
{
  "name": "economy",
  "width": 58,
  "height": 63,
  "attempt": 1,
  "verification": "review-required",
  "feature_results": {
    "handle": true,
    "opening": true
  },
  "artifacts": "artifacts"
}
```

The baseline is last. The recommendation is `balanced` when present, otherwise the middle accepted non-baseline tier, otherwise the first variant.

- [ ] **Step 4: Implement CLI and comparison**

CLI:

```text
python scripts/build_variant_set.py \
  --variants-root <directory> \
  --summary <directory>/summary.json \
  --comparison <directory>/comparison.png
```

The comparison displays each compiled template with name, dimensions, bead count, board layout, and verification state. It does not alter any source pattern.

- [ ] **Step 5: Verify GREEN and commit**

Run the focused test once, then:

```bash
git add \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/variant_set.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/build_variant_set.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/__init__.py \
  tests/test_variant_set.py
git commit -m "feat: validate semantic pattern variants"
```

---

### Task 3: Agent Skill workflow and generic semantic contract

**Files:**
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/semantic-multi-size.md`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/pattern-draft-contract.md`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/input-routing.md`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/output-format.md`
- Modify: `tests/skill-evals/scenarios.md`
- Modify: `tests/skill-evals/with-skill.md`
- Modify: `tests/test_repository.py`

**Interfaces:**
- Consumes Task 1 target planning and Task 2 aggregation.
- Produces baseline-first default behavior and an explicit multi-size branch.

- [ ] **Step 1: Add failing repository contracts**

Require the Skill to:

- finish and deliver a baseline before offering variants on ordinary requests;
- use the approved one-line optional prompt;
- skip that prompt and generate variants when intent includes multi-size, budget, or board comparison;
- read `semantic-multi-size.md`;
- create a task-specific hard/soft feature contract without assuming a person;
- use independent redraws from source + baseline + contract;
- allow one larger retry, cancellation, and adjacent-tier merging;
- run `build_variant_set.py` only after per-tier deterministic compilation.

Require the reference and eval rubrics to cover people/animals, objects, text or logos, landscapes, plants/abstract art, and occluded finished-bead photos.

- [ ] **Step 2: Verify RED**

Run:

```bash
../v0.3-pattern-architecture/.venv/bin/python -m pytest \
  tests/test_repository.py -q
```

Expected: failures because the workflow and reference do not exist.

- [ ] **Step 3: Implement the concise Skill workflow**

Keep the main Skill focused:

1. Detect ordinary versus explicit multi-size intent.
2. Extract task-specific semantic hard/soft features.
3. Deliver one baseline.
4. On an ordinary request, ask the approved one-line optional question after delivery and stop.
5. On explicit or confirmed multi-size intent, plan, independently redraw, compile, validate, and compare accepted variants.

Move JSON shapes, per-source examples, retry/merge rules, CLI commands, and delivery details to `references/semantic-multi-size.md`.

- [ ] **Step 4: Update pattern contracts and eval rubrics**

Replace fixed person-centric identity examples with content-dependent feature language while retaining examples for discoverability. Add explicit non-human scenarios and the real failure baseline: fixed-size resampling flattened detail, while display-pixel over-sampling inflated bead counts.

- [ ] **Step 5: Validate and commit**

Run:

```bash
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
../v0.3-pattern-architecture/.venv/bin/python -m pytest \
  tests/test_sizing.py tests/test_variant_set.py tests/test_repository.py -q
```

Then commit:

```bash
git add \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references \
  tests/skill-evals tests/test_repository.py
git commit -m "feat: add semantic multi-size workflow"
```

---

### Task 4: v0.4.0 documentation, verification, packaging, and publication

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
- Generate: `dist/fuse-bead-designer-plugin-v0.4.0.zip`
- Generate: `dist/create-fuse-bead-patterns-skill-v0.4.0.zip`

**Interfaces:**
- Produces one synchronized `0.4.0` release and immutable `v0.4.0` tag.

- [ ] **Step 1: Add failing version and README assertions**

Require Chinese-first docs to explain:

- baseline-first default behavior;
- the optional one-line multi-size question;
- explicit multi-size requests;
- semantic hard-feature gates for arbitrary image content;
- independent redraw rather than mechanical downsampling;
- two-candidate maximum and two-to-four accepted versions.

Require every version source and default installation ref to be `0.4.0` / `v0.4.0`.

- [ ] **Step 2: Verify RED and update docs/metadata**

Run `tests/test_repository.py` once for RED, then update the listed files. Keep Agent natural-language usage before developer CLI examples.

- [ ] **Step 3: Run final verification once**

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

- [ ] **Step 4: Commit and build archives once**

Commit all source and documentation changes, then run:

```bash
../v0.3-pattern-architecture/.venv/bin/python tools/package_release.py
```

Inspect roots, both Skills, semantic reference, planner/validator scripts, version metadata, privacy exclusions, and SHA-256 values.

- [ ] **Step 5: Publish**

After final diff review:

```bash
git tag -a v0.4.0 -m "Fuse Bead Designer v0.4.0"
git push origin main v0.4.0
git ls-remote origin refs/heads/main refs/tags/v0.4.0 refs/tags/v0.4.0^{}
```

Remote `main` and the peeled tag must resolve to the verified release commit.
