# Input routing / 输入分流

Classify before editing or compiling. The class controls how much semantic work
is permitted; the compiler still creates the only countable grid.

| Source class | Recognize it by | Required handling |
| --- | --- | --- |
| `finished-bead-photo` | Physical round beads, pegboard, camera angle, hands, table, glare, or shadows | Identify the bead subject, exclude interference, correct perspective, and use a clean front-facing intermediate. Do not interpret a hand, board holes, shadow, or reflection as beads. |
| `pixel-art` | Intentional hard-edged logical pixels, often scaled with nearest-neighbor edges | Preserve the original logical grid and subject. Do not reduce it to a decorative smaller grid unless the user explicitly asks for a redesign. |
| `high-resolution-image` | Illustration or photograph with continuous detail, gradients, or no pre-existing cell grid | Identify the single subject, remove background/interference, and make a clean flat subject intermediate before compiler sampling. |

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
- Large occlusion: an occlusion that hides an identity-defining feature, leaves
  more than one credible reconstruction, or prevents a reliable boundary is
  `review-required`. Ask for another photo or user decision; never call its
  quantities confirmed.

## Hosts without image tools

Do not fabricate a clean intermediate. Compile only an already clear,
front-facing, single-subject input with no unresolved interference or occlusion.
Otherwise stop and request a crop, a second angle, a clean source image, or a
user choice. The deterministic compiler can count supplied pixels; it cannot
resolve semantic ambiguity.
