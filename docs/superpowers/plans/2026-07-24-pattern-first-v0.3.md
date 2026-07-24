# Fuse Bead Designer v0.3 Pattern-First Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release v0.3.0 with installation-only first-use wording and a pattern-first compiler/Skill workflow that preserves logical artwork independently from standard board dimensions.

**Architecture:** Source classification selects a real route policy. Pattern dimensions are chosen or recovered before board layout, exact-grid routes use center sampling without automatic cleanup, and high-resolution/obstructed sources require a semantic pattern draft before deterministic compilation. Existing artifacts stay compatible and the old median sampler remains opt-in.

**Tech Stack:** Python 3.10+, Pillow, pytest, JSON Schema, Markdown Agent Skill, Codex Plugin manifest.

## Global Constraints

- Version is exactly `0.3.0`.
- Chinese README is primary; English README provides equivalent information.
- Installation and use are separate; installation must stop before examples, dependency setup, or compilation.
- Pattern dimensions may be any positive integers and are never resized to multiples of 29.
- Board layout is derived as `ceil(width / 29) x ceil(height / 29)` only after pattern dimensions are fixed.
- `pixel-art` and `pattern-draft` default to center sampling with cleanup disabled.
- `high-resolution-image` must not be compiled directly without a pattern draft.
- `finished-bead-photo` must not be compiled directly unless explicitly marked `--rectified-grid`.
- Image generation may design/restore the pattern draft but never supplies authoritative counts, final legend, or verification status.
- Tests follow RED-GREEN-REFACTOR and every task is committed before review.

---

### Task 1: Installation-only natural-language contract

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `AGENTS.md`
- Modify: `tests/test_repository.py`
- Modify: `tests/skill-evals/scenarios.md`
- Modify: `tests/skill-evals/with-skill.md`

**Interfaces:**
- Consumes: current Marketplace/Plugin installation commands.
- Produces: one exact Chinese first-use prompt and one equivalent English prompt; an Agent installation contract that stops after install.

- [ ] **Step 1: Write failing repository assertions**

Add tests asserting that the Chinese README contains:

```text
请安装这个 Codex 插件：https://github.com/MrLQQ/fuse-bead-designer
```

and that `AGENTS.md` states an installation request does not authorize cloning,
running examples, creating virtual environments, or installing runtime
dependencies.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_repository.py -q
```

Expected: failure because the current prompt says `请安装并使用` and the stop
boundary is absent.

- [ ] **Step 3: Implement the minimal documentation contract**

Use this exact primary prompt:

```text
请安装这个 Codex 插件：https://github.com/MrLQQ/fuse-bead-designer 。请由你完成安装；安装成功后停止，不要运行示例或安装额外运行依赖，只提醒我新建任务。
```

Keep the use prompt in a separate section for the new task:

```text
把这张图生成拼豆设计图。
```

Update the English README and forward-eval documents with equivalent semantics.

- [ ] **Step 4: Verify GREEN**

Run the focused repository tests and confirm they pass.

- [ ] **Step 5: Commit**

```bash
git add README.md README.en.md AGENTS.md tests/test_repository.py tests/skill-evals
git commit -m "docs: separate plugin installation from use"
```

### Task 2: Pattern sizing independent from board layout

**Files:**
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/sizing.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/boards.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/__init__.py`
- Modify: `tests/test_boards.py`
- Create: `tests/test_sizing.py`

**Interfaces:**
- Produces:

```python
@dataclass(frozen=True)
class PatternSizeCandidate:
    name: str
    width: int
    height: int
    target_long_side: int

def recommend_pattern_sizes(
    subject_width: int,
    subject_height: int,
    detail_score: float,
) -> tuple[PatternSizeCandidate, ...]

@dataclass(frozen=True)
class BoardLayout:
    pattern_width: int
    pattern_height: int
    module_size: int
    board_columns: int
    board_rows: int

def layout_boards(width: int, height: int, module_size: int = 29) -> BoardLayout
```

- [ ] **Step 1: Write failing sizing and layout tests**

Cover:

```python
assert layout_boards(68, 60).board_columns == 3
assert layout_boards(68, 60).board_rows == 3
assert (layout_boards(68, 60).pattern_width, layout_boards(68, 60).pattern_height) == (68, 60)
```

Also assert recommendations:

- preserve portrait/landscape aspect within one logical cell;
- return `economy`, `balanced`, and `detail`;
- are not all multiples of 29;
- increase monotonically with detail score;
- validate finite positive inputs.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_boards.py tests/test_sizing.py -q
```

Expected: missing `sizing` module and `layout_boards`.

- [ ] **Step 3: Implement minimal sizing and layout**

Use long-side anchors of `48`, `64`, and `80` logical cells, adjusted by at
most `+16` cells from a normalized `detail_score` in `[0, 1]`. Derive the
short side from source aspect ratio and clamp it to at least `1`.

Retain `select_board` only as a deprecated compatibility wrapper. New code must
call `layout_boards` after pattern dimensions are selected.

- [ ] **Step 4: Verify GREEN and refactor**

Run focused tests. Confirm no recommendation code refers to
`STANDARD_CANDIDATES` or `max_boards`.

- [ ] **Step 5: Commit**

```bash
git add plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer tests/test_boards.py tests/test_sizing.py
git commit -m "feat: decouple pattern sizing from board layout"
```

### Task 3: Classification-driven exact-grid compiler

**Files:**
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/routing.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/quantize.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/cli.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/models.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/masking.py`
- Create: `tests/test_routing.py`
- Modify: `tests/test_quantize.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_models.py`

**Interfaces:**
- Produces:

```python
@dataclass(frozen=True)
class RoutePolicy:
    classification: str
    requires_pattern_draft: bool
    sampling: str
    cleanup: bool
    crop_subject: bool

def policy_for(
    classification: str,
    *,
    rectified_grid: bool = False,
) -> RoutePolicy

def sample_cell_centers(
    image: Image.Image,
    mask: Image.Image,
    width: int,
    height: int,
    palette: list[PaletteColor],
    *,
    color_limit: int = 16,
    grid_box: tuple[int, int, int, int] | None = None,
) -> list[list[SampledCell]]
```

- [ ] **Step 1: Write route-policy tests and verify RED**

Assert:

- `pixel-art` and `pattern-draft`: `sampling == "center"`,
  `cleanup is False`;
- `high-resolution-image`: raises an actionable error telling the caller to
  create a pattern draft;
- `finished-bead-photo`: raises unless `rectified_grid=True`;
- rectified finished-bead input uses center sampling and no cleanup.

- [ ] **Step 2: Write exact-grid sampling tests and verify RED**

Create a synthetic scaled logical grid containing a one-cell eye highlight and
transparent padding. Assert that center sampling:

- returns the declared grid dimensions;
- ignores padding after a supplied/cropped grid box;
- preserves the one-cell highlight;
- keeps color totals internally consistent.

- [ ] **Step 3: Implement route policy and center sampler**

Center sampling uses an odd window no larger than 25% of the logical cell's
source rectangle in each direction. It must never average the entire cell
rectangle. Reuse palette matching and color limiting.

- [ ] **Step 4: Rewire the CLI**

Add:

```text
--classification pattern-draft
--grid-box LEFT,TOP,RIGHT,BOTTOM
--rectified-grid
--cleanup
--sampling center|median
```

Rules:

- route policy chooses default sampling and cleanup;
- an explicit compatibility sampling flag may request median sampling;
- `--cleanup` is opt-in;
- explicit `--width` and `--height` are pattern dimensions;
- board layout is calculated with `layout_boards`;
- selection uses the cropped subject, never raw transparent padding;
- reports record `source_classification`, `sampling`, `cleanup`, `grid_box`,
  and board layout.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_routing.py tests/test_quantize.py tests/test_cli.py tests/test_models.py -q
```

- [ ] **Step 6: Commit**

```bash
git add plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer tests/test_routing.py tests/test_quantize.py tests/test_cli.py tests/test_models.py
git commit -m "feat: compile exact grids by source route"
```

### Task 4: Skill workflow and complex quality regression

**Files:**
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/input-routing.md`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/output-format.md`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/pattern-draft-contract.md`
- Create: `tests/fixtures/complex-logical-pattern.png`
- Create: `tests/test_quality_regression.py`
- Modify: `tests/test_repository.py`
- Modify: `tests/skill-evals/scenarios.md`
- Modify: `tests/skill-evals/with-skill.md`

**Interfaces:**
- Consumes: Task 3 CLI route contract.
- Produces: concise Agent procedure for source restoration/design, actual grid
  verification, deterministic compilation, and final visual comparison.

- [ ] **Step 1: Record the existing failing behavior**

In the skill eval, retain the real failure facts as baseline evidence:

- `58 x 58`: 1788 beads, facial detail flattened;
- `87 x 87`: 3970 beads but still less similar than the 2875-bead reference;
- `110 x 122`: 10044 beads due to display-pixel over-sampling.

The expected behavior is not an exact `68 x 60`; it is preservation of identity
features within a practical bead-count band.

- [ ] **Step 2: Add failing Skill contract assertions**

Assert that the Skill:

- says pattern dimensions precede board layout;
- allows image generation/editing to create a semantic pattern draft;
- forbids model-generated counts and final legend;
- branches by source class;
- requires actual grid verification;
- does not default to singleton cleanup for pixel art or pattern drafts.

- [ ] **Step 3: Add the complex fixture and failing regression**

Create a redistributable synthetic dark character with:

- two one-cell bright eyes;
- a three-color forehead ornament;
- thin turquoise edge accents;
- isolated yellow highlights;
- transparent padding.

Compile it through the exact-grid path and assert all named feature coordinates
survive, the output grid equals the source logical grid, totals match, and the
board layout does not resize it.

- [ ] **Step 4: Rewrite the Skill minimally**

Keep `SKILL.md` under 500 lines. Move detailed pattern-draft prompts and
acceptance rules to `pattern-draft-contract.md`.

The high-resolution route must say:

1. design a plain bead-pattern draft with a practical bead budget;
2. preserve silhouette, eyes, facial marks, and signature ornaments;
3. do not ask the model to draw final UI, coordinates, counts, or legend;
4. mechanically verify the actual grid;
5. compile and compare before delivery.

- [ ] **Step 5: Run focused tests and Skill validators**

Run:

```bash
.venv/bin/python -m pytest tests/test_quality_regression.py tests/test_repository.py -q
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
python3 /Users/bytedance/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/fuse-bead-designer
```

- [ ] **Step 6: Commit**

```bash
git add plugins/fuse-bead-designer/skills/create-fuse-bead-patterns tests
git commit -m "feat: make bead design pattern-first"
```

### Task 5: v0.3 documentation, examples, packaging, and release

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `CONTRIBUTING.md`
- Modify: `pyproject.toml`
- Modify: `plugins/fuse-bead-designer/.codex-plugin/plugin.json`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `tools/package_release.py`
- Modify: `tests/test_repository.py`
- Regenerate: `examples/outputs/**`
- Regenerate: `dist/fuse-bead-designer-skill-v0.3.0.zip`
- Regenerate: `dist/fuse-bead-designer-plugin-v0.3.0.zip`

**Interfaces:**
- Consumes: all v0.3 compiler and Skill behavior.
- Produces: public Chinese-first release documentation and deterministic
  installable archives.

- [ ] **Step 1: Write failing version and README assertions**

Assert every manifest/version reference is `0.3.0`, README explains
pattern-first behavior, and command-line use remains an advanced/debugging
section rather than the primary user workflow.

- [ ] **Step 2: Verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_repository.py -q
```

- [ ] **Step 3: Update versions and documentation**

Explain:

- install prompt and new-task boundary;
- natural-language image workflow;
- three source routes;
- pattern size vs board layout;
- deterministic counts;
- limitations and inferred-region handling.

Do not claim automatic direct photo compilation where the semantic-draft route
is required.

- [ ] **Step 4: Regenerate representative examples**

Regenerate examples with the new route flags. Do not use the private user image
as a committed fixture. The public complex fixture may be shown as a regression
example.

- [ ] **Step 5: Run full verification**

Run:

```bash
.venv/bin/python -m pytest -q
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
python3 /Users/bytedance/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/fuse-bead-designer
.venv/bin/python tools/package_release.py
```

Inspect both ZIP roots, embedded manifest versions, and SHA-256 values.

- [ ] **Step 6: Commit**

```bash
git add README.md README.en.md CONTRIBUTING.md pyproject.toml .agents plugins tools tests examples dist
git commit -m "release: prepare fuse bead designer v0.3.0"
```

### Task 6: Independent review and GitHub publication

**Files:**
- Review all changes from merge base through branch HEAD.

**Interfaces:**
- Produces: clean whole-branch review, pushed branch/main state, GitHub URL,
  and release email summary.

- [ ] **Step 1: Run fresh full verification**

Run the full suite, Skill validator, Plugin validator, and deterministic
packaging again after all task fixes.

- [ ] **Step 2: Dispatch independent whole-branch review**

Provide the design, plan, implementation reports, and a full diff package.
Resolve every Critical or Important finding and re-review.

- [ ] **Step 3: Publish**

Because the user explicitly authorized direct GitHub publication, fast-forward
or merge the reviewed branch into `main`, rerun the full suite on `main`, and
push `main` to `origin` without requesting another permission.

- [ ] **Step 4: Send completion email**

Send a concise Chinese summary to `2802351094@qq.com` containing:

- GitHub repository and commit link;
- v0.3.0 changes;
- test/validator results;
- the new installation sentence;
- the new natural-language usage sentence;
- any remaining limitations.

