---
name: create-fuse-bead-patterns
description: Use when turning finished bead photos, pixel art, illustrations, or high-resolution images into 拼豆图纸, 拼豆模板, or 像素拼豆 with compiler-verified color counts, bead quantities, board choices, palettes, and explicit uncertainty.
---

# Create Fuse Bead Patterns

Own the complete workflow. Do not ask the user to run commands or install
runtime dependencies when the host can do so with the available permissions.
Run the bundled compiler yourself and deliver its generated files.

Create a clean semantic input first; compile its cells, counts, and artifacts
with the bundled deterministic compiler. `pattern.json`, not an image model or
a hand-written grid, is the sole source of truth for bead quantities.

## Workflow / 工作流

Perform these steps in order:

1. Inspect the image at full size; do not downsample existing pixel art merely
   to make a smaller pattern.
2. Classify it as `finished-bead-photo`, `pixel-art`, or
   `high-resolution-image`. Read [input-routing.md](references/input-routing.md)
   for routing and stop conditions.
3. Identify one intended subject and every interference source (hands, tools,
   table, shadows, glare, pegboard, reflections, or background). Stop and ask
   the user to choose if multiple plausible subjects remain.
4. Decide whether semantic reconstruction is needed. For a finished-bead photo,
   isolate the beads, remove non-subject interference, and correct perspective.
   For pixel art, preserve its logical pixels. For a high-resolution image,
   make a clean, flat subject intermediate before sampling.
5. Mark uncertainty before compiling. Infer only a small, structurally
   recoverable occlusion; record its cells and use `inferred-low`. A large,
   identity-defining, or unresolved occlusion is `review-required`; stop when
   the host cannot resolve it safely. Never treat a hand as beads.
6. Choose board and palette constraints. Prefer standard 29-cell modules;
   honor explicit size, board-count, and palette instructions. Use only a
   supplied brand/inventory palette when provided; never invent brand codes.
   Read [palette-format.md](references/palette-format.md) when making or using
   a palette file.
7. Run the bundled compiler yourself on the clean subject as described in
   **Internal execution**. Do not manually calculate, copy, or amend counts.
8. Inspect the generated template and report. If
   `report.json` has non-empty `board_decision.alternatives`, render the chosen
   size and every close alternative with `--width` and `--height` into separate
   output directories; ask the user to choose before declaring a final board
   layout. Confirm all reported quantities from `pattern.json`/`colors.csv`.
9. Report artifact paths and the verification state. Use “confirmed” only for
   `verified`; label `inferred-low` as provisional reconstruction and
   `review-required` quantities as provisional pending user confirmation. Read
   [output-format.md](references/output-format.md) for the delivery checklist.

## Internal execution

From this skill directory, run:

```bash
python scripts/create_pattern.py \
  --input <clean-subject.png> \
  --output-dir <output-directory> \
  --verification <verified|inferred-low|review-required> \
  --classification <finished-bead-photo|pixel-art|high-resolution-image>
```

Pass `--removed-interference <description>`, `--palette <palette.json-or-csv>`,
and `--inferred-cells <column,row>` as applicable. Keep a meaningful
single-cell feature with `--protect-cells <column,row>` when cleanup could
erase it.

## Image capability / 图像能力

Use any available image-inspection/editing capability only to make the clean,
front-facing subject intermediate. In Codex, prefer built-in `imagegen` for
semantic editing when needed. Do not ask an image tool to draw the final grid,
legend, labels, or quantity table. Recheck identity, silhouette, key features,
and every inferred region after editing.

Without an image tool, proceed only when the subject, boundary, and cells are
already clear enough to compile; otherwise state what cannot be determined and
ask for a clearer image or user choice. See [input-routing.md](references/input-routing.md).
