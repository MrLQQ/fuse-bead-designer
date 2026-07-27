# Output format / 输出格式

The compiler writes five artifacts. Treat `pattern.json` as canonical; all
other artifacts are derived views or review evidence.

| Artifact | Purpose |
| --- | --- |
| `pattern.json` | Canonical cells, palette IDs, board layout, exact total/per-color counts, inferred cells, and verification state. |
| `template.png` | Buildable grid with coordinates, board boundaries, legend, and quantities. |
| `colors.csv` | Build list: color names, optional supplied brand code, hex value, and compiler-derived exact count. |
| `report.json` | Classification, removed interference, board decision and alternatives, palette decision, cleanup changes, warnings, and verification state. |
| `review.png` | Visual review overlay for inferred/disputed cells; generated when needed. |

## Verification states

- `verified`: No semantic reconstruction changed the subject. Compiler counts
  may be reported as confirmed. `high-resolution-image` cannot use `verified`
  because its semantic pattern draft contains a design decision.
- `inferred-low`: Limited, explainable reconstruction. Include the inferred
  cells and review overlay; identify the result as provisional reconstruction.
- `review-required`: A key region remains uncertain. A candidate pattern may be
  delivered, but every quantity is provisional until the user confirms it.

Before delivery, open `report.json` and `pattern.json`; verify that the reported
state, logical grid dimensions, board decision, total, and per-color counts
match the compiler output. Confirm that board layout was derived after the logical grid was fixed
and did not resize the pattern.

Open `template.png` and compare the compiled template with the source and pattern draft.
Check every task-specific hard semantic feature and every
inferred region. Revise the semantic draft or verified grid and compile again
when a hard feature is flattened, or when the occupied-cell total falls outside
the intended practical bead budget.

For a multi-size delivery, keep the complete compiler artifacts inside every
accepted tier. Also deliver `comparison.png` and `summary.json`; recommend a
version from the validated summary, not from estimated or hand-written counts.
