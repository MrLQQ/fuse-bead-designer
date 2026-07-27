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

1. From this skill directory, run `python scripts/check_update.py` and parse
   its one JSON result. Do not use `--force` during ordinary pattern generation.
   Only surface `update-available` as a concise notice with its returned
   versioned confirmation prompt in the final response; discard `recent`,
   `up-to-date`, and `unavailable`. If the command cannot run or its output is
   unusable, discard it and continue the pattern task. This check never blocks
   classification, compilation, verification, or delivery. Read
   [update-discovery.md](references/update-discovery.md) only when the update
   behavior needs clarification.
2. Inspect the image at full size; do not downsample existing pixel art merely
   to make a smaller pattern.
3. Classify the original as `finished-bead-photo`, `pixel-art`, or
   `high-resolution-image`. `pattern-draft` is the compiler-ready intermediate.
   Read [input-routing.md](references/input-routing.md) and follow that source
   branch and its stop conditions.
4. Identify one intended subject and every interference source (hands, tools,
   table, shadows, glare, pegboard, reflections, or background). Stop and ask
   the user to choose if multiple plausible subjects remain.
5. Prepare the route input. Rectify a finished-bead photo into a declared grid;
   preserve pixel art's logical pixels; use image generation or editing to
   create a semantic pattern draft for a high-resolution image. Follow
   [pattern-draft-contract.md](references/pattern-draft-contract.md) whenever
   creating or restoring a draft.
6. Mark uncertainty before compiling. Infer only a small, structurally
   recoverable occlusion; record its cells and use `inferred-low`. A large,
   identity-defining, or unresolved occlusion is `review-required`; stop when
   the host cannot resolve it safely. Never treat a hand as beads.
7. Verify the actual logical grid mechanically. Requested image dimensions and
   raster display dimensions are not grid evidence. Require declared logical
   dimensions or unique nearest-neighbor recovery. Always fail on ambiguous grid recovery
   instead of treating display pixels as beads.
8. Choose a practical bead budget that preserves silhouette, eyes, facial
   marks, and signature ornaments. Fix the logical pattern dimensions, then
   derive the 29-cell board layout. Honor explicit user constraints, but do not
   force the pattern onto standard-board multiples.
9. Select the palette. Use only a supplied brand/inventory palette when
   provided; never invent brand codes. Read
   [palette-format.md](references/palette-format.md) when making or using a
   palette file.
10. Run the bundled compiler yourself on the verified grid as described in
   **Internal execution**. Do not manually calculate, copy, or amend counts. For
   `pixel-art` and `pattern-draft`, singleton cleanup is disabled by default.
11. Open the generated template and compare it with the source and draft.
    Recheck silhouette and every identity feature before delivery. If the
    practical bead budget was missed or identity was flattened, revise the
    draft/grid and compile again.
12. Report artifact paths and the verification state. Use “confirmed” only for
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

Because the semantic draft contains design decisions that are not confirmed by
the deterministic compiler, `high-resolution-image` cannot use `verified`.
Use `inferred-low` for bounded, coordinate-recorded reconstruction or
`review-required` for other semantic drafts.

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

<!-- high-resolution-command:start -->
Do not use the generic pattern-draft command above for a high-resolution
source. It would lose the original/draft provenance boundary. Use the original
as `--input` and the separate semantic draft as `--draft-input`:

```bash
python scripts/create_pattern.py \
  --input <original-source.png> \
  --output-dir <output-directory> \
  --classification high-resolution-image \
  --draft-input <semantic-pattern-draft.png> \
  --width <verified-logical-columns> \
  --height <verified-logical-rows> \
  --grid-box <left,top,right,bottom> \
  --verification <inferred-low|review-required>
```

Omit `--grid-box` only when the verified logical grid fills the draft image.
The compiler, not either image, produces counts or the final legend.
<!-- high-resolution-command:end -->

For a clean rectified finished-bead grid, use
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
