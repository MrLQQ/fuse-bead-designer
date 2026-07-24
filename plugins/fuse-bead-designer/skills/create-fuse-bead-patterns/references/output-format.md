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
  may be reported as confirmed.
- `inferred-low`: Limited, explainable reconstruction. Include the inferred
  cells and review overlay; identify the result as provisional reconstruction.
- `review-required`: A key region remains uncertain. A candidate pattern may be
  delivered, but every quantity is provisional until the user confirms it.

Before delivery, open `report.json` and `pattern.json`; verify that the reported
state, board decision, total, and per-color counts match the compiler output.
If `board_decision.alternatives` is non-empty, render each close size and get a
user choice before naming a final layout.
