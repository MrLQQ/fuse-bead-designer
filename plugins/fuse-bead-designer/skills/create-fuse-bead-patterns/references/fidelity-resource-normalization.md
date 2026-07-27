# Fidelity and Resource Normalization

Use this gate before compilation whenever the source may contain display-scale
pixels, repeated bead blocks, or more colors than the old generic palette.

## Spatial gate

Distinguish:

- raster pixels: storage or camera resolution;
- observed cells: bead holes, rendered squares, or repeated blocks;
- semantic cells: the smallest square grid that changes the design.

Recover the smallest provable semantic grid. A byte-perfect global `3 × 3`
repeat means one semantic cell was displayed nine times in area; treating all
nine as separate decisions spends nine times the beads without adding detail.
Use the compiler's automatic recovery only for exact nearest-neighbor evidence.
When the evidence is noisy or asymmetric, declare verified dimensions or stop
for review.

Board layout cannot resize the pattern. Derive boards only after the semantic
grid is fixed.

## Color gate

The baseline preserves mapped colors. Do not pass `--colors` for the baseline
unless the user explicitly requested a cap or an economy-oriented variant.
Low-frequency colors can carry outlines, text, highlights, symbols, or material
boundaries and are not disposable merely because they are rare.

When a color cap is explicit:

1. compile the unlimited mapping first;
2. reduce deterministically;
3. report source and final color counts plus changed cells;
4. label color fidelity as `reduced`.

## Delivery evidence

Read `pattern.json.settings.fidelity` and `report.json.fidelity`. Report grid
fidelity, color fidelity, and semantic fidelity independently. Never call a
result fully verified when only its occupancy grid is exact.
