# Fuse Bead Designer v0.1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, validate, document, and publish `MrLQQ/fuse-bead-designer`, an MIT-licensed Codex Plugin containing a portable Agent Skill and a deterministic fuse-bead pattern compiler.

**Architecture:** An image-capable agent performs semantic classification, subject isolation, and explicitly marked occlusion reconstruction. A portable Python/Pillow compiler turns the cleaned subject into a canonical `pattern.json`; PNG, CSV, reports, and review overlays are derived from that one structure.

**Tech Stack:** Python 3.10+, Pillow, pytest, Agent Skills `SKILL.md`, Codex Plugin and Marketplace manifests, GitHub Actions, GitHub CLI for final publication.

## Global Constraints

- Repository: public `MrLQQ/fuse-bead-designer`, default branch `main`, MIT License.
- Chinese `README.md` is the primary GitHub landing page; English lives in `README.en.md`.
- Plugin name: `fuse-bead-designer`; portable skill name: `create-fuse-bead-patterns`.
- Standard board module: 29x29; ask before finalizing more than four boards unless the user already specified the size.
- Default palette size: 8 to 16 colors; never invent a brand color code.
- Empty cells and white beads are separate states.
- `pattern.json` is the only source of truth for rendered templates and counts.
- Dithering is off by default.
- Semantic uncertainty is one of `verified`, `inferred-low`, or `review-required`.
- `review-required` counts are provisional, never confirmed.
- Runtime dependencies are Python standard library plus Pillow where practical.
- Use relative paths; never commit credentials, private inputs, or user images.
- Every production-code behavior follows RED-GREEN-REFACTOR.
- Skill authoring follows baseline-without-skill, implementation, and forward-test-with-skill.

---

## File Responsibility Map

### Repository packaging

- `.agents/plugins/marketplace.json`: repository-backed Codex marketplace.
- `plugins/fuse-bead-designer/.codex-plugin/plugin.json`: plugin identity and UI metadata.
- `plugins/fuse-bead-designer/assets/`: plugin icon, logo, and real screenshots.
- `pyproject.toml`: Python dependency and pytest configuration.
- `LICENSE`: MIT license for 2026 MrLQQ.

### Portable skill

- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md`: semantic workflow, stopping rules, compiler invocation, and validation contract.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/agents/openai.yaml`: skill UI metadata only.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/assets/palettes/generic.json`: generic bilingual palette.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/assets/pattern.schema.json`: canonical pattern schema.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/assets/fonts/NotoSansCJKsc-Regular.otf`: portable bilingual rendering font.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/assets/fonts/OFL.txt`: bundled font license.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/input-routing.md`: detailed input classification and uncertainty rules.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/palette-format.md`: custom palette CSV/JSON contract.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/output-format.md`: JSON, CSV, PNG, and report contracts.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/create_pattern.py`: portable command-line entry point.

### Compiler package

- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/models.py`: dataclasses, validation, counts, serialization.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/boards.py`: standard/custom board scoring.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/palettes.py`: palette loading, validation, and perceptual color distance.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/masking.py`: subject occupancy mask with border-connected background removal.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/quantize.py`: occupied-cell sampling and palette assignment.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/cleanup.py`: confidence-gated conservative cleanup.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/render.py`: template and review PNG rendering.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/io.py`: JSON, CSV, and report writing.
- `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/cli.py`: argument parsing and orchestration.

### Tests, examples, docs, and release

- `tests/conftest.py`: imports the nested portable package and creates reusable images/palettes.
- `tests/test_models.py`: canonical structure and count invariants.
- `tests/test_boards.py`: board scoring and explicit overrides.
- `tests/test_masking.py`: white-bead/background separation.
- `tests/test_palettes.py`: generic and custom palette behavior.
- `tests/test_quantize.py`: deterministic cell assignment.
- `tests/test_cleanup.py`: conservative replacement and protected cells.
- `tests/test_render.py`: derived artifact agreement and PNG layout.
- `tests/test_cli.py`: end-to-end command behavior.
- `tests/test_repository.py`: marketplace, plugin, skill, docs, and example structure.
- `tests/skill-evals/scenarios.md`: raw baseline and forward-test prompts.
- `tests/skill-evals/baseline.md`: observed behavior without the skill.
- `tests/skill-evals/with-skill.md`: observed behavior with the skill.
- `examples/prompts/`: exact image-generation prompts used for public examples.
- `examples/inputs/`: openly distributable generated fixtures.
- `examples/outputs/`: outputs produced by the real compiler.
- `tools/package_release.py`: deterministic plugin and standalone-skill archives.
- `.github/workflows/ci.yml`: test, structure, and packaging checks.
- `README.md`: Chinese-first project introduction and installation guide.
- `README.en.md`: English alternative.
- `CONTRIBUTING.md`: contribution, testing, sample licensing, and privacy rules.

---

### Task 1: Establish Skill Baselines and Public Test Scenarios

**Files:**
- Create: `tests/skill-evals/scenarios.md`
- Create: `tests/skill-evals/baseline.md`
- Create: `examples/prompts/high-resolution-subject.txt`
- Create: `examples/prompts/occluded-finished-beads.txt`

**Interfaces:**
- Consumes: the approved design specification and raw, non-skill task prompts.
- Produces: three stable scenario prompts and recorded baseline failures that the final skill must correct.

- [ ] **Step 1: Define three raw scenarios without revealing the intended solution**

Write `tests/skill-evals/scenarios.md` with these prompts:

```markdown
# Skill Evaluation Scenarios

## A. Existing pixel art
Turn the supplied clean pixel-art subject into a practical fuse-bead template.
Include a grid and exact color quantities.

## B. High-resolution illustration
Turn the supplied non-pixel illustration into a practical fuse-bead template.
Preserve the subject's silhouette and identity.

## C. Occluded finished work
Turn the supplied photograph of finished fuse-bead work into a practical
template. A hand covers part of the subject and the table remains visible.
```

- [ ] **Step 2: Generate two openly distributable raw fixtures with built-in image generation**

Use one built-in `image_gen` call per fixture. Save the exact prompts in the two
files under `examples/prompts/`. The high-resolution prompt must request a clean
non-pixel mascot illustration. The occluded prompt must request a photograph of
physical fuse-bead work with a hand covering a small but non-critical corner.
Keep generated files outside the skill directory until baseline evaluation
finishes so an unskilled agent cannot discover intended outputs.

- [ ] **Step 3: Run baseline agents without the new skill**

Dispatch fresh-context subagents with only one scenario, its raw image, and the
request. Do not pass this plan, the design conclusions, or the expected
failures. Record verbatim whether each agent:

```text
identified the subject
excluded background/hand
marked inferred content
used a deterministic grid representation
made unsupported exact-count claims
```

- [ ] **Step 4: Save observed baseline behavior**

Write `tests/skill-evals/baseline.md` with the heading
`# Baseline behavior without the skill`, followed by one section per completed
run. Each section records the scenario name, observed approach, failure or
success, and verbatim evidence. Do not pre-create empty table rows or write
hypothetical failures.

- [ ] **Step 5: Commit the skill-test baseline**

```bash
git add tests/skill-evals examples/prompts
git commit -m "test: capture fuse bead skill baselines"
```

---

### Task 2: Scaffold the Repository Marketplace, Plugin, and Skill

**Files:**
- Create: `.agents/plugins/marketplace.json`
- Create: `plugins/fuse-bead-designer/.codex-plugin/plugin.json`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/agents/openai.yaml`
- Create: `pyproject.toml`
- Create: `LICENSE`
- Create: `.gitignore`

**Interfaces:**
- Consumes: plugin name `fuse-bead-designer`, skill name `create-fuse-bead-patterns`, MIT license.
- Produces: validator-compatible directories for all later compiler and skill files.

- [ ] **Step 1: Run the required plugin scaffold**

```bash
python3 /Users/bytedance/.codex/skills/.system/plugin-creator/scripts/create_basic_plugin.py \
  fuse-bead-designer \
  --path plugins \
  --with-skills \
  --with-assets \
  --with-marketplace \
  --marketplace-path .agents/plugins/marketplace.json \
  --category Creativity
```

Expected: plugin folder, valid manifest, assets folder, skills folder, and
repository marketplace entry pointing to `./plugins/fuse-bead-designer`.

- [ ] **Step 2: Run the required skill initializer**

```bash
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  create-fuse-bead-patterns \
  --path plugins/fuse-bead-designer/skills \
  --resources scripts,references,assets \
  --interface display_name="Fuse Bead Patterns" \
  --interface short_description="Create count-accurate fuse-bead templates" \
  --interface default_prompt="Use $create-fuse-bead-patterns to turn this image into a count-accurate fuse-bead template."
```

Expected: a new skill folder with `SKILL.md`, resource directories, and
`agents/openai.yaml`.

- [ ] **Step 3: Replace scaffold placeholders with a minimal valid skill shell**

Use this exact frontmatter and keep the body limited to the temporary
development contract:

```markdown
---
name: create-fuse-bead-patterns
description: Use when converting finished fuse-bead photos, pixel art, illustrations, or other reference images into buildable grid templates with exact color quantities.
---

# Create Fuse Bead Patterns

## Development contract

Treat semantic image understanding and deterministic pattern compilation as
separate stages. Do not claim exact counts until the compiler has produced
`pattern.json`. The complete workflow is added after the compiler interfaces
are verified.
```

- [ ] **Step 4: Add Python and repository configuration**

Write `pyproject.toml`:

```toml
[project]
name = "fuse-bead-designer"
version = "0.1.0"
description = "Deterministic compiler bundled with the Fuse Bead Designer Agent Skill"
requires-python = ">=3.10"
dependencies = ["Pillow>=10.0"]

[project.optional-dependencies]
test = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

Write `.gitignore`:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
dist/
work/
*.egg-info/
```

Write the standard MIT license with `Copyright (c) 2026 MrLQQ`.

- [ ] **Step 5: Verify scaffold structure**

Run:

```bash
python3 /Users/bytedance/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/fuse-bead-designer
```

Expected: PASS.

Run:

```bash
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
```

Expected: PASS.

- [ ] **Step 6: Commit the scaffold**

```bash
git add .agents plugins pyproject.toml LICENSE .gitignore
git commit -m "chore: scaffold fuse bead plugin and skill"
```

---

### Task 3: Implement the Canonical Pattern Model

**Files:**
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/__init__.py`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/models.py`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/assets/pattern.schema.json`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`

**Interfaces:**
- Produces: `PaletteColor`, `Pattern`, `CompileReport`, `VerificationState`, `Pattern.validate()`, `Pattern.color_counts()`, and `Pattern.to_dict()`.
- Canonical empty-cell value: `None`; occupied cells contain a palette identifier string.

- [ ] **Step 1: Make the nested portable package importable in tests**

Write `tests/conftest.py`:

```python
from pathlib import Path
import sys


SCRIPT_ROOT = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "fuse-bead-designer"
    / "skills"
    / "create-fuse-bead-patterns"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_ROOT))
```

- [ ] **Step 2: Write the failing model tests**

```python
from fuse_bead_designer.models import PaletteColor, Pattern, VerificationState


def test_white_bead_is_distinct_from_empty_cell():
    pattern = Pattern(
        width=2,
        height=1,
        module_size=29,
        palette=[PaletteColor("white", "White", "白色", "#F7F4EA")],
        cells=[[None, "white"]],
        verification=VerificationState.VERIFIED,
        is_custom_size=True,
    )

    assert pattern.color_counts() == {"white": 1}
    assert pattern.total_beads == 1
    assert pattern.to_dict()["cells"] == [[None, "white"]]


def test_pattern_rejects_unknown_palette_identifier():
    pattern = Pattern(
        width=1,
        height=1,
        module_size=29,
        palette=[],
        cells=[["missing"]],
        verification=VerificationState.VERIFIED,
        is_custom_size=True,
    )

    with pytest.raises(ValueError, match="unknown palette id"):
        pattern.validate()
```

- [ ] **Step 3: Run the tests and verify RED**

Run:

```bash
pytest tests/test_models.py -v
```

Expected: collection fails because `fuse_bead_designer.models` does not exist.

- [ ] **Step 4: Implement the minimal canonical model**

Implement:

```python
from collections import Counter
from dataclasses import asdict, dataclass, field
from enum import Enum


class VerificationState(str, Enum):
    VERIFIED = "verified"
    INFERRED_LOW = "inferred-low"
    REVIEW_REQUIRED = "review-required"


@dataclass(frozen=True)
class PaletteColor:
    id: str
    name: str
    name_zh: str
    hex: str
    brand_code: str | None = None


@dataclass
class Pattern:
    width: int
    height: int
    module_size: int
    palette: list[PaletteColor]
    cells: list[list[str | None]]
    verification: VerificationState
    board_columns: int = 1
    board_rows: int = 1
    is_custom_size: bool = False
    inferred_cells: list[tuple[int, int]] = field(default_factory=list)
    settings: dict[str, object] = field(default_factory=dict)

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("grid dimensions must be positive")
        if len(self.cells) != self.height:
            raise ValueError("cell row count does not match height")
        if any(len(row) != self.width for row in self.cells):
            raise ValueError("cell column count does not match width")
        palette_ids = [color.id for color in self.palette]
        if len(palette_ids) != len(set(palette_ids)):
            raise ValueError("duplicate palette id")
        known = set(palette_ids)
        for row in self.cells:
            for cell in row:
                if cell is not None and cell not in known:
                    raise ValueError(f"unknown palette id: {cell}")
        for column, row in self.inferred_cells:
            if not (0 <= column < self.width and 0 <= row < self.height):
                raise ValueError("inferred cell is outside the grid")

    def color_counts(self) -> dict[str, int]:
        self.validate()
        counts = Counter(
            cell for row in self.cells for cell in row if cell is not None
        )
        return dict(sorted(counts.items()))

    @property
    def total_beads(self) -> int:
        return sum(self.color_counts().values())

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "width": self.width,
            "height": self.height,
            "module_size": self.module_size,
            "board_layout": {
                "columns": self.board_columns,
                "rows": self.board_rows,
                "is_custom_size": self.is_custom_size,
            },
            "palette": [asdict(color) for color in self.palette],
            "cells": self.cells,
            "total_beads": self.total_beads,
            "color_counts": self.color_counts(),
            "verification": self.verification.value,
            "inferred_cells": [list(cell) for cell in self.inferred_cells],
            "settings": self.settings,
        }


@dataclass
class CompileReport:
    classification: str
    removed_interference: list[str]
    board_decision: dict[str, object]
    palette_decision: dict[str, object]
    cleanup_changes: list[tuple[int, int]]
    warnings: list[str]
    verification: VerificationState

    def to_dict(self) -> dict[str, object]:
        return {
            "classification": self.classification,
            "removed_interference": self.removed_interference,
            "board_decision": self.board_decision,
            "palette_decision": self.palette_decision,
            "cleanup_changes": [list(cell) for cell in self.cleanup_changes],
            "warnings": self.warnings,
            "verification": self.verification.value,
        }
```

Validation must reject non-positive dimensions, wrong row/column counts,
duplicate palette IDs, unknown cell IDs, and inferred coordinates outside the
grid. It must also reject non-positive board rows/columns and standard board
layouts whose dimensions do not equal `29 * board_columns` by
`29 * board_rows`. `to_dict()` must include schema version `1`.

- [ ] **Step 5: Add the matching JSON schema**

The schema must require:

```json
{
  "schema_version": 1,
  "width": 29,
  "height": 29,
  "module_size": 29,
  "board_layout": {"columns": 1, "rows": 1, "is_custom_size": false},
  "palette": [],
  "cells": [],
  "total_beads": 0,
  "color_counts": {},
  "verification": "verified",
  "inferred_cells": [],
  "settings": {}
}
```

Constrain `verification` to the three approved values and cell values to
`string` or `null`.

- [ ] **Step 6: Run tests and verify GREEN**

```bash
pytest tests/test_models.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add plugins/fuse-bead-designer/skills/create-fuse-bead-patterns tests
git commit -m "feat: add canonical pattern model"
```

---

### Task 4: Implement Standard Board Selection

**Files:**
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/boards.py`
- Create: `tests/test_boards.py`

**Interfaces:**
- Consumes: source aspect ratio, optional explicit size, preferred maximum of four boards.
- Produces: `BoardSelection(width, height, board_columns, board_rows, is_custom, requires_confirmation, score, alternatives)`.

- [ ] **Step 1: Write failing board-selection tests**

```python
def test_wide_subject_prefers_two_horizontal_boards():
    selected = select_board(subject_width=1600, subject_height=800)
    assert (selected.width, selected.height) == (58, 29)
    assert selected.requires_confirmation is False


def test_square_subject_defaults_to_one_board_when_detail_is_low():
    selected = select_board(1000, 1000, detail_score=0.2)
    assert (selected.width, selected.height) == (29, 29)


def test_explicit_custom_size_wins():
    selected = select_board(1000, 1000, explicit_size=(40, 36))
    assert (selected.width, selected.height) == (40, 36)
    assert selected.is_custom is True


def test_more_than_four_boards_requires_confirmation():
    selected = select_board(1800, 1200, detail_score=1.0, max_boards=6)
    assert selected.board_count > 4
    assert selected.requires_confirmation is True
```

- [ ] **Step 2: Run RED**

```bash
pytest tests/test_boards.py -v
```

Expected: FAIL because `select_board` is missing.

- [ ] **Step 3: Implement candidate scoring**

Use candidates `(29,29)`, `(58,29)`, `(29,58)`, `(58,58)`, `(87,58)`, and
`(58,87)`. `BoardSelection` also exposes an `alternatives` tuple containing
candidate dimensions whose score is within `0.05` of the selected score, so
the skill can render and present close choices. Score with:

```python
aspect_loss = abs(log((width / height) / source_aspect))
detail_penalty = max(0.0, detail_score - min(width, height) / 58)
board_penalty = 0.08 * max(0, board_count - 1)
score = aspect_loss + detail_penalty + board_penalty
```

Explicit sizes bypass candidate scoring. Set `requires_confirmation` when
`board_count > 4`.

Add a test that a deliberately balanced source exposes at least one close
alternative and assert every alternative is one of the standard candidates.

- [ ] **Step 4: Run GREEN and full regression**

```bash
pytest tests/test_boards.py tests/test_models.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/boards.py tests/test_boards.py
git commit -m "feat: select standard fuse bead boards"
```

---

### Task 5: Implement Subject Masking and Palette Mapping

**Files:**
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/masking.py`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/palettes.py`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/assets/palettes/generic.json`
- Create: `tests/test_masking.py`
- Create: `tests/test_palettes.py`

**Interfaces:**
- Produces: `derive_subject_mask(image, tolerance=18) -> Image.Image`, `load_palette(path=None) -> list[PaletteColor]`, `nearest_color(rgb, palette) -> ColorMatch`.
- `ColorMatch` contains `color_id`, `distance`, and `exact`.

- [ ] **Step 1: Write failing white/background separation test**

```python
def test_border_connected_white_is_empty_but_enclosed_warm_white_is_subject():
    image = Image.new("RGB", (7, 7), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((1, 1, 5, 5), fill="#111515")
    draw.point((3, 3), fill="#F7F4EA")

    mask = derive_subject_mask(image)

    assert mask.getpixel((0, 0)) == 0
    assert mask.getpixel((3, 3)) == 255
```

- [ ] **Step 2: Write failing palette tests**

```python
def test_generic_palette_contains_bilingual_unique_ids():
    palette = load_palette()
    assert 8 <= len(palette)
    assert len({color.id for color in palette}) == len(palette)
    assert all(color.name and color.name_zh for color in palette)


def test_custom_palette_rejects_duplicate_brand_codes(tmp_path):
    path = tmp_path / "palette.json"
    path.write_text(json.dumps([
        {"id": "a", "name": "A", "name_zh": "甲", "hex": "#000000", "brand_code": "01"},
        {"id": "b", "name": "B", "name_zh": "乙", "hex": "#FFFFFF", "brand_code": "01"}
    ]))
    with pytest.raises(ValueError, match="duplicate brand code"):
        load_palette(path)
```

- [ ] **Step 3: Run RED**

```bash
pytest tests/test_masking.py tests/test_palettes.py -v
```

Expected: FAIL because masking and palette modules do not exist.

- [ ] **Step 4: Implement border-connected background masking**

For images with alpha, occupancy is `alpha > 0`. For opaque images, sample the
four corners, flood-fill only border-connected pixels whose perceptual distance
from the median corner color is at most `tolerance`, and invert the result.
Internal white regions therefore remain occupied.

- [ ] **Step 5: Implement palette loading and perceptual matching**

The bundled palette must contain stable generic IDs, English/Chinese names, and
hex values. Convert sRGB to CIE Lab before nearest-color matching. Validate
hex syntax, unique IDs, and unique non-empty brand codes.

Use this exact initial 16-color generic palette:

```json
[
  {"id":"black","name":"Black","name_zh":"黑色","hex":"#111515"},
  {"id":"charcoal","name":"Charcoal","name_zh":"炭黑","hex":"#273033"},
  {"id":"gray","name":"Gray","name_zh":"灰色","hex":"#596564"},
  {"id":"warm-white","name":"Warm White","name_zh":"暖白","hex":"#F7F4EA"},
  {"id":"red","name":"Red","name_zh":"红色","hex":"#E53935"},
  {"id":"orange","name":"Orange","name_zh":"橙色","hex":"#FB8C00"},
  {"id":"yellow","name":"Yellow","name_zh":"黄色","hex":"#FFE000"},
  {"id":"lime","name":"Lime","name_zh":"荧光绿","hex":"#69E51C"},
  {"id":"green","name":"Green","name_zh":"绿色","hex":"#00B66A"},
  {"id":"dark-green","name":"Dark Green","name_zh":"深绿","hex":"#087A52"},
  {"id":"turquoise","name":"Turquoise","name_zh":"青绿","hex":"#00CFC1"},
  {"id":"blue","name":"Blue","name_zh":"蓝色","hex":"#2684FF"},
  {"id":"purple","name":"Purple","name_zh":"紫色","hex":"#8E44AD"},
  {"id":"pink","name":"Pink","name_zh":"粉色","hex":"#FF6FAE"},
  {"id":"brown","name":"Brown","name_zh":"棕色","hex":"#76503A"},
  {"id":"tan","name":"Tan","name_zh":"浅棕","hex":"#C49A6C"}
]
```

- [ ] **Step 6: Run GREEN**

```bash
pytest tests/test_masking.py tests/test_palettes.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add plugins/fuse-bead-designer/skills/create-fuse-bead-patterns tests
git commit -m "feat: separate subjects and map bead palettes"
```

---

### Task 6: Implement Deterministic Quantization and Conservative Cleanup

**Files:**
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/quantize.py`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/cleanup.py`
- Create: `tests/test_quantize.py`
- Create: `tests/test_cleanup.py`

**Interfaces:**
- Produces: `sample_cells(image, mask, width, height, palette) -> list[list[SampledCell]]`.
- Produces: `cleanup_cells(cells, protected_cells=frozenset()) -> CleanupResult`.
- `CleanupResult` contains cleaned cells and changed `(column, row)` coordinates.

- [ ] **Step 1: Write failing deterministic quantization test**

```python
def test_quantization_is_deterministic_and_has_no_dithering():
    image, mask = two_color_subject()
    first = sample_cells(image, mask, 29, 29, load_palette())
    second = sample_cells(image, mask, 29, 29, load_palette())
    assert first == second
    assert {cell.color_id for row in first for cell in row if cell.occupied} <= {
        color.id for color in load_palette()
    }
```

- [ ] **Step 2: Write failing cleanup tests**

```python
def test_low_confidence_singleton_inside_consensus_is_replaced():
    cells = consensus_grid(center_color="yellow", center_distance=90.0)
    result = cleanup_cells(cells)
    assert result.cells[1][1].color_id == "black"
    assert result.changed_cells == [(1, 1)]


def test_protected_singleton_is_preserved():
    cells = consensus_grid(center_color="yellow", center_distance=90.0)
    result = cleanup_cells(cells, protected_cells={(1, 1)})
    assert result.cells[1][1].color_id == "yellow"
    assert result.changed_cells == []
```

- [ ] **Step 3: Run RED**

```bash
pytest tests/test_quantize.py tests/test_cleanup.py -v
```

Expected: FAIL because quantize and cleanup modules are missing.

- [ ] **Step 4: Implement cell sampling**

For each output cell:

- calculate its source rectangle;
- determine occupancy from median mask coverage, requiring at least 50%;
- take median RGB across occupied source pixels;
- map through `nearest_color`;
- retain perceptual distance as cleanup confidence;
- never diffuse error into neighboring cells.

After initial mapping, if more than `color_limit` palette IDs are present, keep
the most frequent IDs and remap cells using removed IDs to their nearest kept
color. Break frequency ties by palette ID so repeated runs remain deterministic.
Add a test that a custom palette with 20 colors produces at most 16 occupied
color IDs when `color_limit=16`.

- [ ] **Step 5: Implement confidence-gated cleanup**

Replace a non-protected occupied cell only when all conditions hold:

```text
at least 6 of 8 occupied neighbors share one color
current color differs from that consensus
current perceptual match distance is at least 1.5x neighbor median distance
cell is not on the outer grid edge
```

Never add or remove occupancy during cleanup. Return every changed coordinate.

- [ ] **Step 6: Run GREEN and regression**

```bash
pytest tests/test_quantize.py tests/test_cleanup.py tests/test_masking.py tests/test_palettes.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer tests
git commit -m "feat: quantize patterns without color noise"
```

---

### Task 7: Render and Write All Derived Artifacts

**Files:**
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/render.py`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/io.py`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/assets/fonts/NotoSansCJKsc-Regular.otf`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/assets/fonts/OFL.txt`
- Create: `tests/test_render.py`

**Interfaces:**
- Consumes: validated `Pattern`, optional `CompileReport`.
- Produces: `template.png`, `pattern.json`, `colors.csv`, `report.json`, and conditional `review.png`.

- [ ] **Step 1: Write failing artifact-agreement test**

```python
def test_written_artifacts_share_exact_counts(tmp_path, sample_pattern):
    write_artifacts(sample_pattern, tmp_path)

    data = json.loads((tmp_path / "pattern.json").read_text())
    rows = list(csv.DictReader((tmp_path / "colors.csv").open()))

    assert data["total_beads"] == sum(int(row["count"]) for row in rows)
    assert (tmp_path / "template.png").exists()
    assert not (tmp_path / "review.png").exists()


def test_inferred_pattern_writes_review_overlay(tmp_path, inferred_pattern):
    write_artifacts(inferred_pattern, tmp_path)
    assert (tmp_path / "review.png").exists()
```

- [ ] **Step 2: Write failing visual-structure test**

```python
def test_template_contains_grid_and_legend(sample_pattern):
    image = render_template(sample_pattern, cell_size=18)
    assert image.width > sample_pattern.width * 18
    assert image.height >= sample_pattern.height * 18
    assert image.getbbox() is not None
```

- [ ] **Step 3: Run RED**

```bash
pytest tests/test_render.py -v
```

Expected: FAIL because render and IO functions are missing.

- [ ] **Step 4: Implement the renderer**

Download `NotoSansCJKsc-Regular.otf` from the official
`notofonts/noto-cjk` repository and copy its `Sans/LICENSE` file to
`assets/fonts/OFL.txt`. Record the upstream repository, font filename, and SIL
Open Font License in `CONTRIBUTING.md`. Do not substitute an unlicensed system
font.

Draw from `Pattern.cells` only:

- colored cell rectangles;
- thin grid lines every cell;
- stronger lines every five cells;
- board boundaries at each 29-cell module edge for standard layouts;
- row/column labels;
- legend swatches, bilingual color names, hex/brand code, and counts;
- total beads and board count.

Bundle `NotoSansCJKsc-Regular.otf` and its SIL Open Font License under the
skill's assets. Use that font for English and Chinese template labels so
rendering is portable and cannot degrade to missing-glyph boxes.

- [ ] **Step 5: Implement structured writers**

Use UTF-8 JSON with `ensure_ascii=False`. Write CSV columns:

```text
id,name,name_zh,hex,brand_code,count
```

`report.json` must include classification, removed interference, board
decision, palette decision, cleanup changes, warnings, and verification state.
Only write `review.png` when inferred cells or cleanup review markers exist.

- [ ] **Step 6: Run GREEN**

```bash
pytest tests/test_render.py tests/test_models.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer tests/test_render.py
git commit -m "feat: render count-accurate bead templates"
```

---

### Task 8: Build and Verify the Portable CLI

**Files:**
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/cli.py`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/create_pattern.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Command: `python scripts/create_pattern.py --input INPUT --output-dir DIR [options]`.
- Options: `--width`, `--height`, `--max-boards`, `--palette`, `--colors`, `--verification`, `--inferred-cells`, `--protect-cells`, `--classification`, `--removed-interference`.

- [ ] **Step 1: Write failing CLI integration test**

```python
def test_cli_creates_all_verified_outputs(tmp_path, clean_subject_path):
    output = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input", str(clean_subject_path),
            "--output-dir", str(output),
            "--width", "29",
            "--height", "29",
            "--verification", "verified",
            "--classification", "pixel-art",
        ],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert {p.name for p in output.iterdir()} == {
        "template.png", "pattern.json", "colors.csv", "report.json"
    }
```

- [ ] **Step 2: Write failing confirmation-guard test**

```python
def test_cli_refuses_unconfirmed_large_board(tmp_path, clean_subject_path):
    result = run_cli(
        clean_subject_path,
        tmp_path,
        "--width", "87",
        "--height", "87",
    )
    assert result.returncode == 2
    assert "more than four boards" in result.stderr
```

- [ ] **Step 3: Run RED**

```bash
pytest tests/test_cli.py -v
```

Expected: FAIL because the CLI does not exist.

- [ ] **Step 4: Implement CLI orchestration**

Use `argparse`. Require both width and height when either is supplied. Reject
`--colors` outside 8 through 16. Parse coordinates as `column,row` pairs.
Require `--confirm-large-board` for more than four standard boards. Never
overwrite a non-empty output directory unless `--force` is provided.

- [ ] **Step 5: Run GREEN and full compiler suite**

```bash
pytest tests/test_models.py tests/test_boards.py tests/test_masking.py tests/test_palettes.py tests/test_quantize.py tests/test_cleanup.py tests/test_render.py tests/test_cli.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts tests/test_cli.py
git commit -m "feat: add portable fuse bead compiler CLI"
```

---

### Task 9: Complete the Portable Skill and Forward Tests

**Files:**
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/SKILL.md`
- Modify: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/agents/openai.yaml`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/input-routing.md`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/palette-format.md`
- Create: `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/references/output-format.md`
- Create: `tests/skill-evals/with-skill.md`

**Interfaces:**
- Consumes: the verified CLI, baseline failures, and approved uncertainty rules.
- Produces: a concise skill that routes semantic work and always uses the deterministic compiler for final counts.

- [ ] **Step 1: Convert baseline failures into explicit skill requirements**

For every observed baseline failure, add one positive workflow requirement to
`SKILL.md`. The workflow order must be:

```text
inspect image
classify input
identify subject and interference
decide whether semantic reconstruction is needed
mark uncertainty
choose board/palette constraints
run create_pattern.py
inspect generated template and report
report paths and provisional/confirmed status
```

- [ ] **Step 2: Write detailed references**

`input-routing.md` must define the three source classes, multi-subject stop,
small/large occlusion boundary, and host-without-image-tool fallback.

`palette-format.md` must include one complete generic JSON example and one CSV
example with:

```text
id,name,name_zh,hex,brand_code
```

`output-format.md` must define the five artifacts and the three verification
states.

- [ ] **Step 3: Keep `SKILL.md` concise and executable**

The frontmatter description stays trigger-focused. The body points to
references only when needed and includes the exact portable command:

```bash
python scripts/create_pattern.py \
  --input <clean-subject.png> \
  --output-dir <output-directory> \
  --verification <verified|inferred-low|review-required> \
  --classification <finished-bead-photo|pixel-art|high-resolution-image>
```

Codex-specific guidance prefers built-in `imagegen` for semantic editing, but
the core workflow describes capabilities rather than hard-coding an API.
When `BoardSelection.alternatives` is non-empty, require rendering the selected
size and each close alternative, then ask the user to choose before declaring
the final board layout.

- [ ] **Step 4: Validate the skill**

```bash
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
```

Expected: PASS.

- [ ] **Step 5: Run forward tests with fresh agents**

Use the same scenario intent and raw inputs from Task 1. Give each fresh agent
only:

```text
Use $create-fuse-bead-patterns at
plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
to solve this request: <scenario prompt>
```

Record whether each forward run satisfies all requirements. Do not leak the
baseline diagnosis or intended answer.

- [ ] **Step 6: Close observed workflow gaps and rerun**

If an agent skips classification, treats a hand as beads, omits uncertainty,
or invents counts, revise only the instruction responsible for that failure and
rerun the same scenario. Save evidence in `tests/skill-evals/with-skill.md`.

- [ ] **Step 7: Commit**

```bash
git add plugins/fuse-bead-designer/skills/create-fuse-bead-patterns tests/skill-evals
git commit -m "feat: teach agents to create verified bead patterns"
```

---

### Task 10: Produce Open Examples and Plugin Presentation Assets

**Files:**
- Create: `examples/inputs/high-resolution-mascot.png`
- Create: `examples/inputs/occluded-finished-beads.png`
- Create: `examples/outputs/high-resolution-mascot/`
- Create: `examples/outputs/occluded-finished-beads/`
- Create: `plugins/fuse-bead-designer/assets/icon.png`
- Create: `plugins/fuse-bead-designer/assets/screenshot-template.png`
- Modify: `plugins/fuse-bead-designer/.codex-plugin/plugin.json`

**Interfaces:**
- Consumes: generated public fixtures and the real compiler.
- Produces: honest screenshots and optional generated branding referenced by the plugin manifest.

- [ ] **Step 1: Promote only approved generated fixtures**

Copy the two generated images from Task 1 into `examples/inputs/`. Do not copy
the user's private attachment or any third-party artwork. Keep their exact
prompts under `examples/prompts/`.

- [ ] **Step 2: Generate an original plugin icon with built-in image generation**

Use case: `logo-brand`. Request a simple square icon made from a small cluster
of colorful round fuse beads forming a clean pixel-grid sparkle on a neutral
background, with no words, letters, watermark, brand logo, or existing
character. Inspect it, crop it square if needed, and save it as
`plugins/fuse-bead-designer/assets/icon.png`.

- [ ] **Step 3: Run the real compiler on the public inputs**

Use the skill workflow and compiler. For the occluded input, include inferred
cell coordinates and use `inferred-low` or `review-required` based on actual
visual inspection. Save all artifacts under `examples/outputs/`.

- [ ] **Step 4: Create the plugin screenshot from the real output**

Copy the best real `template.png` to
`plugins/fuse-bead-designer/assets/screenshot-template.png`. Do not use image
generation for this screenshot.

- [ ] **Step 5: Fill plugin metadata**

Set:

```json
{
  "name": "fuse-bead-designer",
  "version": "0.1.0",
  "description": "Create reviewable, count-accurate fuse-bead templates from reference images.",
  "author": {
    "name": "MrLQQ",
    "url": "https://github.com/MrLQQ"
  },
  "repository": "https://github.com/MrLQQ/fuse-bead-designer",
  "homepage": "https://github.com/MrLQQ/fuse-bead-designer#readme",
  "license": "MIT",
  "keywords": ["fuse-beads", "pixel-art", "craft-patterns", "agent-skill"],
  "skills": "./skills/",
  "interface": {
    "displayName": "Fuse Bead Designer",
    "shortDescription": "Create count-accurate fuse-bead templates",
    "longDescription": "Convert finished bead photos, pixel art, and high-resolution images into reviewable templates with deterministic grids and exact color quantities.",
    "developerName": "MrLQQ",
    "category": "Creativity",
    "capabilities": ["Image Understanding", "Pattern Generation"],
    "websiteURL": "https://github.com/MrLQQ/fuse-bead-designer",
    "defaultPrompt": [
      "Turn this image into a practical fuse-bead template.",
      "Convert this finished bead photo into a count-accurate pattern."
    ],
    "brandColor": "#16A085",
    "composerIcon": "./assets/icon.png",
    "logo": "./assets/icon.png",
    "screenshots": ["./assets/screenshot-template.png"]
  }
}
```

Omit privacy-policy and terms URLs because the repository has no hosted
service and no separate policy pages.

- [ ] **Step 6: Validate assets and manifest**

```bash
python3 /Users/bytedance/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/fuse-bead-designer
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add examples plugins/fuse-bead-designer/assets plugins/fuse-bead-designer/.codex-plugin/plugin.json
git commit -m "docs: add honest examples and plugin artwork"
```

---

### Task 11: Write Chinese-First Documentation, CI, and Release Packaging

**Files:**
- Create: `README.md`
- Create: `README.en.md`
- Create: `CONTRIBUTING.md`
- Create: `tests/test_repository.py`
- Create: `tools/package_release.py`
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: verified installation instructions and two deterministic release archives.

- [ ] **Step 1: Write failing repository-contract tests**

```python
def test_chinese_readme_is_primary():
    chinese = Path("README.md").read_text()
    english = Path("README.en.md").read_text()
    assert "[English](README.en.md)" in chinese
    assert "[中文](README.md)" in english
    assert "安装" in chinese


def test_marketplace_points_to_plugin():
    data = json.loads(Path(".agents/plugins/marketplace.json").read_text())
    entry = next(item for item in data["plugins"] if item["name"] == "fuse-bead-designer")
    assert entry["source"]["path"] == "./plugins/fuse-bead-designer"


def test_documented_example_outputs_agree():
    for path in Path("examples/outputs").glob("*/pattern.json"):
        data = json.loads(path.read_text())
        assert data["total_beads"] == sum(data["color_counts"].values())
```

- [ ] **Step 2: Run RED**

```bash
pytest tests/test_repository.py -v
```

Expected: FAIL because documentation and packaging files are missing.

- [ ] **Step 3: Write Chinese `README.md` first**

Use this order:

```text
language switch
project title and one-sentence outcome
real template screenshot
why the project exists
supported inputs and uncertainty boundary
quick start for Codex Plugin
standalone Skill installation
other Agent Skills-compatible tools
usage examples
outputs
board sizing
generic and brand palettes
known limitations
development and tests
contributing
license
```

The English document mirrors the facts but does not need literal sentence-level
translation. Test every command shown in both documents.

- [ ] **Step 4: Write installation commands**

Codex repository-marketplace installation:

```bash
git clone https://github.com/MrLQQ/fuse-bead-designer.git
cd fuse-bead-designer
codex plugin marketplace add "$PWD"
codex plugin add fuse-bead-designer@personal
```

Standalone skill installation:

```bash
cp -R plugins/fuse-bead-designer/skills/create-fuse-bead-patterns \
  "${CODEX_HOME:-$HOME/.codex}/skills/"
```

State that other tools must support the Agent Skills format and may use a
different skills directory.

- [ ] **Step 5: Implement deterministic release packaging**

`tools/package_release.py` must create:

```text
dist/fuse-bead-designer-plugin-v0.1.0.zip
dist/create-fuse-bead-patterns-skill-v0.1.0.zip
```

Use `zipfile.ZipFile` with sorted relative paths. Exclude `__pycache__`,
`.DS_Store`, and generated private work directories. Preserve the plugin root
inside the plugin archive and the skill root inside the standalone archive.

- [ ] **Step 6: Add CI**

Use `actions/checkout@v6`, `actions/setup-python@v6`, and
`actions/upload-artifact@v7`, matching the current official action
documentation. Use a Python matrix of 3.10, 3.11, and 3.12. Install with:

```bash
python -m pip install -e ".[test]"
```

Run:

```bash
pytest -q
python tools/package_release.py
```

Upload both archives as CI artifacts named
`fuse-bead-release-python-${{ matrix.python-version }}`.

- [ ] **Step 7: Run GREEN**

```bash
pytest tests/test_repository.py -v
python tools/package_release.py
```

Expected: tests PASS and both archives exist.

- [ ] **Step 8: Run the complete local suite**

```bash
pytest -q
```

Expected: all tests PASS with no warnings.

- [ ] **Step 9: Commit**

```bash
git add README.md README.en.md CONTRIBUTING.md tests/test_repository.py tools .github
git commit -m "docs: publish Chinese-first project guide"
```

---

### Task 12: Final Validation, GitHub Publication, and v0.1.0 Release

**Files:**
- Modify only if validation exposes a specific defect.
- Create through GitHub: public repository and release metadata.

**Interfaces:**
- Consumes: clean, fully tested `main` branch and release archives.
- Produces: public `MrLQQ/fuse-bead-designer` and GitHub Release `v0.1.0`.

- [ ] **Step 1: Run all local verification**

```bash
git status --short
git diff --check
pytest -q
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
python3 /Users/bytedance/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/fuse-bead-designer
python tools/package_release.py
```

Expected: clean status before packaging, no whitespace errors, all tests PASS,
both validators PASS, and two archives in `dist/`.

- [ ] **Step 2: Confirm the release diff and commit history**

```bash
git status -sb
git log --oneline --decorate -12
```

Expected: only ignored `dist/` output is untracked/ignored and all intended
changes are committed.

- [ ] **Step 3: Establish secure GitHub CLI authentication**

Current preflight has no `gh` executable and no connected GitHub App account.
Install GitHub CLI only after the required system approval, then run:

```bash
gh auth login --web
gh auth status
```

Expected: authenticated as `MrLQQ`. If the account differs, stop without
creating a repository.

- [ ] **Step 4: Create and push the public repository**

```bash
gh repo create MrLQQ/fuse-bead-designer \
  --public \
  --source . \
  --remote origin \
  --push \
  --description "Turn reference images into reviewable, count-accurate fuse-bead templates."
```

Expected: repository created, `origin` configured, and `main` pushed.

- [ ] **Step 5: Inspect remote state**

```bash
git remote -v
git status -sb
gh repo view MrLQQ/fuse-bead-designer --json nameWithOwner,visibility,defaultBranchRef,url
```

Expected: owner/name is `MrLQQ/fuse-bead-designer`, visibility is `PUBLIC`,
default branch is `main`, and local branch tracks `origin/main`.

- [ ] **Step 6: Create the initial release**

```bash
gh release create v0.1.0 \
  dist/fuse-bead-designer-plugin-v0.1.0.zip \
  dist/create-fuse-bead-patterns-skill-v0.1.0.zip \
  --repo MrLQQ/fuse-bead-designer \
  --title "Fuse Bead Designer v0.1.0" \
  --notes "首个开源版本：提供 Codex Plugin、可独立安装的 Agent Skill、确定性网格编译器、颜色数量统计与不确定性标记。"
```

Expected: public `v0.1.0` release with both archives.

- [ ] **Step 7: Verify public installation instructions against a fresh clone**

Clone to a new temporary directory, run tests and packaging there, and verify
the documented marketplace path resolves. Do not modify the primary checkout.

```bash
git clone https://github.com/MrLQQ/fuse-bead-designer.git <temporary-directory>
python -m pip install -e "<temporary-directory>[test]"
pytest -q <temporary-directory>/tests
```

Expected: PASS.

- [ ] **Step 8: Final handoff**

Report:

```text
repository URL
release URL
main commit SHA
test count and result
skill validator result
plugin validator result
plugin archive URL
standalone skill archive URL
known limitations
```

For the marketplace-backed plugin, include Codex app View and Share links using
the actual local marketplace path, as required by `plugin-creator`.
