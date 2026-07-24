# Task 4 report: Skill workflow and complex quality regression

## Scope

- Rewrote the Skill around source-class routing, pattern dimensions before
  board layout, mechanically verified logical grids, deterministic compilation,
  and final source/draft/template comparison.
- Added `references/pattern-draft-contract.md` for image-generation/editing
  prompts and acceptance rules while keeping `SKILL.md` at 113 lines.
- Added a redistributable synthetic dark-character fixture. It contains a
  `37 x 41` logical grid rendered at `4x`, 8-pixel transparent display padding,
  two one-cell eyes, a three-color forehead ornament, thin turquoise edges, and
  isolated yellow highlights. No private user image is included.
- Added repository contract assertions, the real quality-failure evidence, and
  an exact-grid quality regression. No README, version, release archive, or
  example output was changed.

## RED evidence

1. First repository contract run:

   ```text
   .venv/bin/python -m pytest tests/test_repository.py -q
   1 failed, 13 passed
   missing: Fix pattern dimensions before deriving board layout.
   ```

2. After adding the real baseline-evidence assertion:

   ```text
   .venv/bin/python -m pytest tests/test_repository.py -q
   2 failed, 13 passed
   missing: 58/87/110 failure evidence and the pattern-first Skill contract
   ```

3. The pattern-draft reference assertion failed independently because
   `references/pattern-draft-contract.md` did not exist.

4. The initial synthetic fixture exposed the exact-route source-resolution
   guard:

   ```text
   .venv/bin/python -m pytest tests/test_quality_regression.py -q
   1 failed
   center sampling requires at least 4 source pixels per logical cell in each direction
   ```

   The fixture, not production code, was corrected from 1 source pixel/cell to
   a byte-preserving `4x` nearest-neighbor representation with transparent
   display padding. The logical art and named feature coordinates stayed the
   same.

The retained historical no-skill baseline is:

- `58 x 58`: 1788 beads; facial detail was flattened.
- `87 x 87`: 3970 beads; still less similar than the 2875-bead reference.
- `110 x 122`: 10044 beads; display pixels were over-sampled as beads.

## GREEN evidence

Focused tests:

```text
.venv/bin/python -m pytest tests/test_quality_regression.py tests/test_repository.py -q
17 passed in 0.53s
```

The complex fixture compiles through `pattern-draft` with explicit
`--width 37 --height 41 --grid-box 8,8,156,172`. The regression proves:

- all `37 x 41` output cells equal the source logical grid;
- all named eyes, ornament colors, edge accents, and highlights survive;
- 840 occupied cells remain inside the practical 700-950 band;
- total beads equal the sum of color counts and occupied source cells;
- cleanup changes are empty;
- the board layout is derived as `2 x 2` without resizing the art.

Validators:

```text
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
Skill is valid!

python3 /Users/bytedance/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/fuse-bead-designer
Plugin validation passed
```

Full suite:

```text
.venv/bin/python -m pytest -q
215 passed in 11.13s
```

## Self-review

- `git diff --check` passed.
- The Skill uses the actual Task 3 CLI route flags and keeps model-produced
  artwork separate from compiler-produced dimensions, counts, legend, board
  layout, and verification.
- The fixture is synthetic and redistributable; visual inspection and
  coordinate assertions cover its identity features.
- Task 5 scope remains untouched.

## Reviewer fix: high-resolution provenance command

The reviewer found that the generic `pattern-draft|pixel-art` command plus an
instruction to “add” high-resolution flags could lead an Agent to pass the
semantic draft as both `--input` and `--draft-input`, losing original-source
provenance.

RED:

```text
.venv/bin/python -m pytest \
  tests/test_repository.py::test_skill_high_resolution_command_preserves_original_and_draft_provenance -q
1 failed
missing: <!-- high-resolution-command:start -->
```

GREEN:

```text
.venv/bin/python -m pytest tests/test_repository.py -q
17 passed in 0.18s

python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
Skill is valid!
```

`SKILL.md` now states that the generic pattern-draft command is not the
high-resolution command and gives a complete invocation with
`--input <original-source.png>`,
`--classification high-resolution-image`,
`--draft-input <semantic-pattern-draft.png>`, verified logical dimensions, and
an optional verified grid box. Counts and the final legend remain deterministic
compiler outputs.
