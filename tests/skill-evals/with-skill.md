# Forward evaluation with the skill

Run each scenario in a fresh context with only its raw fixture and this prompt:

```text
Use $create-fuse-bead-patterns at
plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
to solve this request: <scenario prompt>
```

## Pass rubric

Mark a run passing only when it classifies the source, identifies the subject,
excludes interference, routes ambiguity/occlusion correctly, invokes
`scripts/create_pattern.py`, and takes quantities only from generated
`pattern.json`/`colors.csv`. It must report output paths and a matching
verification state; it must not invent a brand code or hand-written counts.

| Public scenario | Required evidence | Pass condition |
| --- | --- | --- |
| `examples/inputs/clean-pixel-art.png` | Classification `pixel-art`; blue cat identified; compiler artifacts | Preserve the logical pixel-art subject rather than silently collapsing it; report compiler-derived quantities. |
| `examples/inputs/high-resolution-mascot.png` | Classification `high-resolution-image`; clean-subject handling; compiler artifacts | Preserve the red-panda librarian's identity/silhouette; state sampling uncertainty if semantic detail is simplified; report compiler-derived quantities. |
| `examples/inputs/occluded-finished-beads.png` | Classification `finished-bead-photo`; hand/table excluded; inferred-cell evidence or stop | Do not count the hand/table; mark a small recoverable tentacle reconstruction `inferred-low`, or use `review-required`/stop if it cannot be safely recovered. |

## Evidence record

Final forward check:

| Scenario | Result | Evidence |
| --- | --- | --- |
| Clean pixel art | PASS | `examples/outputs/clean-pixel-art/`; `pixel-art`, `verified`, 333 compiler-counted beads. |
| High-resolution mascot | PASS | `examples/outputs/high-resolution-mascot/`; `high-resolution-image`, `verified`, 1234 compiler-counted beads. |
| Occluded finished beads | PASS with required review | Raw photo retained in `examples/inputs/`; semantic cleanup retained in `examples/intermediates/`; hand, table, pegboard, glare, shadows, and background are recorded as removed. `review-required` keeps the 1525-bead result explicitly provisional. |

For every output, `pattern.json.total_beads`, the sum of
`pattern.json.color_counts`, and the sum of `colors.csv` counts agree. No
example contains an inferred brand code.
