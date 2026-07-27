# Fidelity and Resource Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recover the smallest provable semantic grid and preserve baseline colors unless the user explicitly requests reduction.

**Architecture:** `logical_grid.py` owns lossless scale recovery and exposes scale evidence. `quantize.py` maps all colors by default and applies an optional explicit reducer. `cli.py` selects the policy, computes fidelity evidence, and writes it into existing pattern/report JSON.

**Tech Stack:** Python 3.12, Pillow, pytest, JSON.

## Global Constraints

- No production change without a failing behavior test.
- Board size never determines the logical grid.
- Default compilation has no color-count cap.
- Explicit color reduction remains deterministic.
- Existing artifact filenames remain compatible.

---

### Task 1: Lossless semantic-grid normalization

**Files:**
- Modify: `tests/test_logical_grid.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/logical_grid.py`

**Interfaces:**
- Consumes: `PIL.Image.Image`
- Produces: `recover_nearest_neighbor_grid(image) -> GridSpec` with `scale` and `area_factor`.

- [ ] Add failing tests proving composite 4× scale and exact 3× repeated grids recover the smallest semantic grid.
- [ ] Run `work/conda-env/bin/python -m pytest tests/test_logical_grid.py -q` and verify the new tests fail because recovery is ambiguous or scale evidence is missing.
- [ ] Change recovery to select the largest byte-perfect uniform scale while retaining square-axis and anti-aliasing guards.
- [ ] Re-run the focused test file and verify it passes.

### Task 2: Fidelity-first color policy

**Files:**
- Modify: `tests/test_quantize.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/quantize.py`

**Interfaces:**
- Consumes: sampled cells, palette, optional positive `color_limit`.
- Produces: all mapped colors when the limit is `None`; deterministic reduced cells when explicit.

- [ ] Replace the default-16 expectation with a failing test that preserves 20 source colors.
- [ ] Run the focused quantization test and verify it fails with 16 colors.
- [ ] Make `color_limit` optional and expose deterministic `limit_colors`.
- [ ] Re-run `tests/test_quantize.py` and verify it passes.

### Task 3: CLI fidelity evidence

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/cli.py`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/models.py`

**Interfaces:**
- Consumes: optional `--colors N`, grid recovery evidence, pre/post reduction cells.
- Produces: `settings.fidelity` and `report.json.fidelity` with grid/color/semantic status and counts.

- [ ] Add failing CLI tests for omitted color limit, explicit limits above 16, 21-color preservation, and 3× grid evidence.
- [ ] Run the new CLI tests and verify failures come from the old default/range/report.
- [ ] Change CLI default to `None`, accept any positive integer, sample before optional reduction, and compute changed-cell evidence.
- [ ] Add fidelity serialization to `CompileReport` and pattern settings.
- [ ] Run focused CLI/model tests and verify they pass.

### Task 4: Plugin behavior contract and verification

**Files:**
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/fidelity-resource-normalization.md`
- Modify: `tests/test_repository.py`

**Interfaces:**
- Consumes: the new compiler behavior.
- Produces: agent instructions that default to semantic-grid normalization and fidelity-first colors.

- [ ] Add a focused repository behavior check for the new reference.
- [ ] Document the two mandatory gates and link the reference from the skill.
- [ ] Run focused logical-grid, quantization, CLI, model, and repository tests.
- [ ] Run the full suite once and inspect `git diff --check`.
