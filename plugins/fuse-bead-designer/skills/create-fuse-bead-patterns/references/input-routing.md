# Input routing / 输入分流

Classify the original before editing or compiling. The source class selects a
real workflow branch; the compiler still creates the only countable grid.

| Source class | Recognize it by | Required handling |
| --- | --- | --- |
| `finished-bead-photo` | Physical round beads, pegboard, camera angle, hands, table, glare, or shadows | Identify the bead subject, exclude interference, correct perspective, and produce a clean front-facing declared grid. Compile only with `--rectified-grid`, paired `--width`/`--height`, and optional `--grid-box`. Do not interpret a hand, board holes, shadow, or reflection as beads. |
| `pixel-art` | Intentional hard-edged logical pixels, often scaled with nearest-neighbor edges | Preserve logical pixels and intentional empty cells. Verify its logical dimensions, then compile with paired `--width`/`--height`; automatic recovery is allowed only when uniquely provable. |
| `high-resolution-image` | Illustration or photograph with continuous detail, gradients, or no pre-existing cell grid | Create a plain semantic pattern draft first; compile the original only through `--draft-input` with verified draft dimensions. Never sample the high-resolution original directly into a final grid. This classification cannot use `verified`; select `inferred-low` or `review-required`. |
| `pattern-draft` | Plain grid-aligned intermediate produced by restoration or semantic design | Compile the exact declared logical grid with paired `--width`/`--height` and optional `--grid-box`. Do not redesign it during deterministic compilation. |

For any route that creates or restores artwork, define hard and soft semantic
features from the actual image content before editing. Do not substitute a
fixed checklist of human facial features for image understanding.

## Grid evidence and route defaults

- Verify the actual logical grid from declared dimensions or one unique,
  byte-for-byte nearest-neighbor scale. Requested image-model dimensions are
  not evidence.
- Uniform, anti-aliased, or multiply valid scales fail on ambiguous grid
  recovery. Ask for/verify dimensions; never use display pixels as beads.
- `pixel-art`, `pattern-draft`, and rectified finished-bead grids use center
  sampling. Automatic singleton cleanup is disabled by default so one-cell
  eyes, highlights, ornaments, thin edges, and intentional empty cells survive.
- A `high-resolution-image` semantic draft records a design decision, not a
  confirmed observation. It cannot use `verified`; use `inferred-low` only for
  bounded, coordinate-recorded reconstruction and otherwise use
  `review-required`.
- Fix pattern dimensions before deriving board layout. Standard 29-cell boards
  tile the verified art afterward and never resize it.

## Subject and occlusion decisions

- One visually dominant subject: continue after recording the excluded
  interference.
- Multiple plausible subjects, overlapping candidate subjects, or unclear
  requested target: stop and ask the user which subject to convert. Do not pick
  by convenience.
- Small occlusion: infer only when it covers a non-identity-defining, bounded
  region and visible silhouette, symmetry, or repeated motif makes the cells
  reproducible. Mark every inferred cell, set `inferred-low`, and explain the
  basis in the report.
- Large occlusion: an occlusion that hides a hard semantic feature, leaves
  more than one credible reconstruction, or prevents a reliable boundary is
  `review-required`. Ask for another photo or user decision; never call its
  quantities confirmed.

## Hosts without image tools

Do not fabricate a clean intermediate. Compile only an already clear,
front-facing, single-subject input with no unresolved interference or occlusion.
Otherwise stop and request a crop, a second angle, a clean source image, or a
user choice. A high-resolution source still requires a semantic pattern draft.
The deterministic compiler can count verified logical cells; it cannot resolve
semantic or grid ambiguity.
