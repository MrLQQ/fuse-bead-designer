# Forward evaluation with the skill

Run each pattern-generation scenario in a fresh context with only its raw fixture and this prompt:

```text
Use $create-fuse-bead-patterns at
plugins/fuse-bead-designer/skills/create-fuse-bead-patterns
to solve this request: <scenario prompt>
```

Run the installation-only scenario in a fresh context without a source fixture.
It must stop after completing installation and reminding the user to start a
new task; it must not clone, run examples, create a virtual environment, or
install runtime dependencies.

## Pattern-generation pass rubric

This rubric applies only to pattern-generation scenarios. Mark a run passing
only when it classifies the source, identifies the subject,
excludes interference, routes ambiguity/occlusion correctly, invokes
`scripts/create_pattern.py`, and takes quantities only from generated
`pattern.json`/`colors.csv`. It must report output paths and a matching
verification state; it must not invent a brand code or hand-written counts.

The installation-only scenario is evaluated only by the separate installation rubric below.

| Public scenario | Required evidence | Pass condition |
| --- | --- | --- |
| `examples/inputs/clean-pixel-art.png` | Classification `pixel-art`; blue cat identified; compiler artifacts | Preserve the logical pixel-art subject rather than silently collapsing it; report compiler-derived quantities. |
| `examples/inputs/high-resolution-mascot.png` | Classification `high-resolution-image`; clean-subject handling; compiler artifacts | Preserve the red-panda librarian's identity/silhouette; state sampling uncertainty if semantic detail is simplified; report compiler-derived quantities. |
| `examples/inputs/occluded-finished-beads.png` | Classification `finished-bead-photo`; hand/table excluded; inferred-cell evidence or stop | Do not count the hand/table; mark a small recoverable tentacle reconstruction `inferred-low`, or use `review-required`/stop if it cannot be safely recovered. |

### Complex quality regression

Retain the no-skill baseline as evidence:

- `58 x 58`: 1788 beads; facial detail was flattened.
- `87 x 87`: 3970 beads; still less similar than the 2875-bead reference.
- `110 x 122`: 10044 beads; display pixels were over-sampled as beads.

A passing run creates/restores a semantic pattern draft, verifies its actual
logical grid, and compiles that grid without singleton cleanup. It preserves
the named identity features within a practical bead-count band. Success is not
an exact `68 x 60` grid, and board layout must not resize the chosen pattern.
All counts and the final legend come from compiler artifacts, not the image
model.

## Semantic multi-size pass rubric

- A baseline-first ordinary request delivers one compiled baseline before the
  optional question and does not pre-generate unused variants.
- An explicit multi-size request proceeds immediately.
- Every source receives a task-specific hard/soft contract. Evaluation coverage
  includes people or animals, objects, text or logos, buildings or landscapes,
  plants or abstract art, and occluded finished-bead photos.
- Each tier is independently redrawn from source + baseline + contract;
  mechanical downsampling is not accepted as a final pattern.
- A hard-feature failure gets at most one larger retry. Persistent failures are
  cancelled; materially equivalent adjacent tiers are merged.
- The final two to four versions are compiled independently and then validated
  with `scripts/build_variant_set.py`.

## Installation-only pass rubric

| Public scenario | Required evidence | Pass condition |
| --- | --- | --- |
| Installation-only first use | Permission-aware Marketplace and Plugin installation; stop boundary | Complete only installation, then remind the user to start a new task; do not clone, run examples, create a virtual environment, or install runtime dependencies. |

## Update-discovery pass rubric

Run these scenarios in fresh contexts. The checker and update Skill may use
their normal host integration, but no scenario may turn an ambiguous request
into a write.

| Public scenario | Required evidence | Pass condition |
| --- | --- | --- |
| Ordinary pattern generation | `recent` or `up-to-date` checker result; normal compiler delivery | Do not surface an update message or delay the pattern result. |
| Available update notice | `update-available` result and the returned versioned confirmation sentence | Finish the requested pattern work, then show a concise notice; do not install, remove, or rebind anything. |
| Offline update checking | `unavailable` checker result | Continue the requested pattern work without an update notice and without a failed-check error presented as a blocker. |
| Unconfirmed update request | Fresh stable-version check and an exact returned confirmation sentence | A generic update request makes no writes; ask for the exact returned sentence for the current stable version. |
| Confirmed exact stable version update | Exact returned confirmation, target-version verification, and host safety approval when requested | Update only Fuse Bead Designer to that stable tag, verify the installed version, then stop and require a new task. |

## Evidence record

Final forward check:

| Scenario | Result | Evidence |
| --- | --- | --- |
| Clean pixel art | PASS | `examples/outputs/clean-pixel-art/`; exact 16 × 16 `pixel-art`, `verified`, 97 compiler-counted beads. |
| High-resolution mascot | PASS with required review | `examples/outputs/high-resolution-mascot/`; `high-resolution-image`, `review-required`, 1234 compiler-counted beads. |
| Occluded finished beads | PASS with required review | Raw photo retained in `examples/inputs/`; semantic cleanup retained in `examples/intermediates/`; hand, table, pegboard, glare, shadows, and background are recorded as removed. `review-required` keeps the 1525-bead result explicitly provisional. |

For every output, `pattern.json.total_beads`, the sum of
`pattern.json.color_counts`, and the sum of `colors.csv` counts agree. No
example contains an inferred brand code.
