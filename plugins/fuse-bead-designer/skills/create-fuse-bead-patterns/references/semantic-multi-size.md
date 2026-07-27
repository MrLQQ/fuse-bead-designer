# Semantic multi-size patterns / 语义多尺寸图纸

Use this branch only when the user explicitly asks for multiple sizes, bead
budget or board-count comparison, or accepts the optional offer after baseline
delivery.

## First principle

Each accepted size is a separate semantic pixel redesign.
Fixed-ratio downsampling, box averaging, median sampling, and generic low-resolution
resampling may inform a preview but must never become a final design. Those
methods either erase small meaning-bearing details or turn display pixels into
extra beads.

Each candidate must use the **source + accepted baseline + feature contract**.
Never create the next tier by shrinking the previous tier.

## Task-specific feature contract

Write `feature-contract.json` before drawing variants:

```json
{
  "subject": "short description of the intended subject",
  "features": [
    {
      "id": "stable-machine-id",
      "description": "visual fact that must remain recognizable",
      "importance": "hard"
    },
    {
      "id": "secondary-detail",
      "description": "detail that may simplify to control cost",
      "importance": "soft"
    }
  ]
}
```

Derive features from the image rather than from a universal subject template:

- **people or animals**: pose, face layout, expression, markings, limbs, tail,
  clothing, or species-defining shapes;
- **objects**: silhouette, handle, opening, controls, wheels, material blocks,
  negative space, or brand-independent construction;
- **text or logos**: readable glyph topology, stroke junctions, counters,
  spacing, and distinctive color geometry;
- **buildings or landscapes**: skyline, roofline, horizon, major masses,
  perspective cues, windows, paths, or focal landmarks;
- **plants or abstract art**: leaf/branch arrangement, rhythm, color balance,
  symmetry or deliberate asymmetry, and negative space;
- **occluded finished-bead photos**: visible grid structure, motif repetition,
  subject boundary, and separately recorded uncertain cells.

Loss of a hard feature rejects the candidate. A soft feature may be simplified
only when the result still communicates the same subject and composition.

## Candidate policy

1. Keep the already accepted baseline unchanged.
2. Plan advisory economy, balanced, and detail targets below the baseline.
   Dimensions are soft targets and are never rounded to 29-cell board
   multiples.
3. Independently redraw each candidate from the source, accepted baseline, and
   feature contract.
4. Compare the candidate against every hard feature. If it fails, allow one initial candidate and one larger retry only.
5. Cancel the tier if the larger retry still fails. Do not deliver a
   meaningless small version merely to preserve a label.
6. Merge adjacent tiers when their dimensions, bead counts, and visible
   information are materially equivalent.
7. Deliver two to four accepted versions, including the baseline. Fewer
   valid versions are better than forced duplicates or damaged art.

Only the Agent judges semantic preservation. The bundled validator checks that
the Agent recorded a Boolean result for every feature and that all compiler
data agree; it does not pretend to perform visual understanding.

## Compile each accepted candidate

Fix the candidate's logical width and height before board calculation. Compile
every accepted redraw independently:

```bash
python scripts/create_pattern.py \
  --input <semantic-candidate.png> \
  --output-dir <variants-root>/<tier>/artifacts \
  --width <verified-logical-columns> \
  --height <verified-logical-rows> \
  --verification review-required \
  --classification pattern-draft
```

Do not pass `--cleanup`. Use shared palette IDs across tiers; a tier may use
only the subset it needs. Write `<tier>/manifest.json` after visual review:

```json
{
  "name": "economy",
  "width": 58,
  "height": 63,
  "attempt": 1,
  "verification": "review-required",
  "feature_results": {
    "handle": true,
    "opening": true
  },
  "artifacts": "artifacts"
}
```

Semantic redesigns are always `review-required`. Only a baseline whose logical
cells were mechanically recovered without semantic change may remain
`verified`.

## Validate and compare

After all per-tier `scripts/create_pattern.py` runs are complete, build the
variant set:

```bash
python scripts/build_variant_set.py \
  --variants-root <variants-root> \
  --summary <variants-root>/summary.json \
  --comparison <variants-root>/comparison.png
```

The command recounts cells and CSV quantities, verifies 29 x 29 board coverage,
checks explicit hard-feature results and the two-attempt limit, and creates a
display-only comparison. It never changes source patterns.

Deliver every accepted tier's `template.png`, `colors.csv`, `pattern.json`, and
`review.png`, plus `comparison.png` and `summary.json`. State why a requested
tier was enlarged, cancelled, or merged.
