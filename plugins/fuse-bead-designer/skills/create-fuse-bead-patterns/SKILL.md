---
name: create-fuse-bead-patterns
description: Use when a user provides a finished bead photo, pixel art, illustration, or high-resolution image and asks for 拼豆图纸, 拼豆模板, 像素拼豆, a fuse-bead pattern, or bead quantities.
---

# Create Fuse Bead Patterns

Own the complete workflow. Do not ask the user to run commands. Run the
bundled compiler yourself and deliver its generated files.

Host capability or permission is not installation approval.
Request approval before installing a missing runtime dependency.
After approval, install it internally; do not ask the user to copy or run the
installation command.

Create or restore a clean logical pattern first, then compile its cells, counts,
board layout, and artifacts deterministically. `pattern.json`, not an image
model or a hand-written grid, is the sole source of truth for bead quantities.

**Fix pattern dimensions before deriving board layout.** A 29-cell board is
manufacturing metadata, never a target used to resample the art.

## Workflow / 工作流

Perform these steps in order:

1. Inspect the image at full size; do not downsample existing pixel art merely
   to make a smaller pattern.
2. Classify the original as `finished-bead-photo`, `pixel-art`, or
   `high-resolution-image`. `pattern-draft` is the compiler-ready intermediate.
   Read [input-routing.md](references/input-routing.md) and follow that source
   branch and its stop conditions.
3. Identify one intended subject and every interference source (hands, tools,
   table, shadows, glare, pegboard, reflections, or background). Stop and ask
   the user to choose if multiple plausible subjects remain.
4. Prepare the route input. Rectify a finished-bead photo into a declared grid;
   preserve pixel art's logical pixels; use image generation or editing to
   create a semantic pattern draft for a high-resolution image. Follow
   [pattern-draft-contract.md](references/pattern-draft-contract.md) whenever
   creating or restoring a draft.
5. Mark uncertainty before compiling. Infer only a small, structurally
   recoverable occlusion; record its cells and use `inferred-low`. A large,
   identity-defining, or unresolved occlusion is `review-required`; stop when
   the host cannot resolve it safely. Never treat a hand as beads.
6. Verify the actual logical grid mechanically. Requested image dimensions and
   raster display dimensions are not grid evidence. Require declared logical
   dimensions or unique nearest-neighbor recovery. Always fail on ambiguous grid recovery
   instead of treating display pixels as beads.
7. Choose a practical bead budget that preserves silhouette, eyes, facial
   marks, and signature ornaments. Fix the logical pattern dimensions, then
   derive the 29-cell board layout. Honor explicit user constraints, but do not
   force the pattern onto standard-board multiples.
8. Select the palette. Use only a supplied brand/inventory palette when
   provided; never invent brand codes. Read
   [palette-format.md](references/palette-format.md) when making or using a
   palette file.
9. Run the bundled compiler yourself on the verified grid as described in
   **Internal execution**. Do not manually calculate, copy, or amend counts. For
   `pixel-art` and `pattern-draft`, singleton cleanup is disabled by default.
10. Open the generated template and compare it with the source and draft.
    Recheck silhouette and every identity feature before delivery. If the
    practical bead budget was missed or identity was flattened, revise the
    draft/grid and compile again.
11. Report artifact paths and the verification state. Use “confirmed” only for
   `verified`; label `inferred-low` as provisional reconstruction and
   `review-required` quantities as provisional pending user confirmation. Read
   [output-format.md](references/output-format.md) for the delivery checklist.

## High-resolution route

1. Design a plain bead-pattern draft with a practical bead budget.
2. Preserve silhouette, eyes, facial marks, and signature ornaments.
3. Never ask an image model to generate counts or the final legend. Do not ask
   it for final UI, coordinates, or verification claims.
4. Verify the actual logical grid mechanically.
5. Compile it deterministically and compare before delivery.

## Internal execution

From this skill directory, compile an exact route with declared, verified
dimensions. For a `pattern-draft` or `pixel-art` input:

```bash
python scripts/create_pattern.py \
  --input <logical-grid.png> \
  --output-dir <output-directory> \
  --width <logical-columns> \
  --height <logical-rows> \
  --verification <verified|inferred-low|review-required> \
  --classification <pattern-draft|pixel-art>
```

For a high-resolution original plus semantic draft, add
`--classification high-resolution-image --draft-input <draft.png>`. For a
clean rectified finished-bead grid, use
`--classification finished-bead-photo --rectified-grid`. Add
`--grid-box LEFT,TOP,RIGHT,BOTTOM` when the logical grid has display padding.

Pass `--removed-interference`, `--palette`, and `--inferred-cells` as
applicable. Do not pass `--cleanup` unless the user explicitly requests
compatibility cleanup and its effect has been reviewed.

## Image capability / 图像能力

Image generation or editing may isolate/rectify a subject, restore a small
occlusion, or create the semantic pattern draft. It may decide which visual
details survive simplification. Never ask an image model to generate counts or
the final legend; deterministic code owns coordinates, palette mapping,
quantities, board layout, and final rendering.

Without an image tool, proceed only when the subject, boundary, and cells are
already clear enough to compile; otherwise state what cannot be determined and
ask for a clearer image or user choice. See [input-routing.md](references/input-routing.md).
