# Pattern draft contract / 图案草稿契约

Use this contract when a high-resolution source needs semantic simplification,
or a finished-bead photo needs limited restoration after rectification. The
output is a plain grid-aligned design intermediate, not a finished template.

## Draft request

Give the image generation/editing tool these positive requirements:

1. Create one flat, front-facing fuse-bead pattern draft on a transparent or
   plain background.
2. Target a practical occupied-cell budget and choose enough logical cells to
   preserve the subject rather than forcing a 29-cell board multiple.
3. Preserve the silhouette, two-sided asymmetries, eyes, facial marks,
   signature ornaments, thin edge accents, and isolated highlights.
4. Use one flat color per logical cell with hard nearest-neighbor edges and no
   gradients, lighting, texture, shadows, peg holes, or faux bead circles.
5. Return only the semantic artwork.

Do not request final UI, board seams, coordinates, labels, color counts,
quantity tables, a legend, or verification claims. Those are deterministic
compiler outputs.

## Acceptance before compilation

- Compare the draft with the source at full size. Every identity feature named
  in the request must still be recognizable.
- Determine the actual logical columns and rows mechanically. A dimension
  requested from the image tool is a design target, not proof of the returned
  grid.
- Accept automatic nearest-neighbor recovery only when exactly one nontrivial
  scale re-expands byte-for-byte. Otherwise declare and verify paired
  dimensions or regenerate the draft; never count display pixels as cells.
- Preserve intentional transparent cells inside the logical canvas. Use a
  `--grid-box` only for display padding outside that canvas.
- Record inferred restored cells and set `inferred-low`. Stop with
  `review-required` if an identity-defining region has more than one credible
  reconstruction.

After acceptance, compile with center sampling and cleanup disabled, then
compare `template.png` with both the source and this draft.
