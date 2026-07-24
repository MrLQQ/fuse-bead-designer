[中文](README.md)

# Fuse Bead Designer

Turn reference images into reviewable fuse-bead patterns. A deterministic compiler derives the grid, counts, and report from one canonical `pattern.json`.

![Real template example](plugins/fuse-bead-designer/assets/screenshot-template.png)

## Why this project exists

Finished-bead photos, pixel art, and illustrations can contain backgrounds, shadows, occlusion, and continuous colors. This project separates semantic image work from deterministic compilation: an Agent prepares a clean subject, then the local Python/Pillow compiler produces count-consistent artifacts.

## Supported inputs and uncertainty boundary

Supported inputs are clean pixel art, high-resolution subject images, and finished fuse-bead photos. The compiler consumes a cleaned subject; it does not reliably solve complex semantics, severe perspective, or large occlusions by itself.

An Agent must mark small, explainable reconstruction with coordinates and a `review.png`. `verified` means no semantic reconstruction affected the subject; `inferred-low` means limited reconstruction; `review-required` means a key region is uncertain. Counts in `review-required` are provisional, not confirmed material quantities. Brand codes are never invented: `brand_code` is retained only when supplied in your palette.

## Quick start: Codex Plugin

```bash
git clone https://github.com/MrLQQ/fuse-bead-designer.git
cd fuse-bead-designer
codex plugin marketplace add "$PWD"
codex plugin add fuse-bead-designer@personal
```

In an image-capable Codex conversation, invoke `$create-fuse-bead-patterns` to prepare a clean, front-facing subject, then run the local compiler below. Without image capability, stop for user review when the subject or an occlusion is unresolved.

## Standalone Agent Skill installation

```bash
cp -R plugins/fuse-bead-designer/skills/create-fuse-bead-patterns \
  "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## Other Agent Skills-compatible tools

Any tool supporting the [Agent Skills](https://agentskills.io/) format can use `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns`. Its skills directory, activation method, and image-tool support are host-specific. This Skill does not replace host image understanding or editing.

## Usage examples

Install the dependencies, then compile the public pixel-art fixture to one 29 × 29 board:

```bash
python -m pip install -e ".[test]"
python plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/create_pattern.py \
  --input examples/inputs/clean-pixel-art.png \
  --output-dir work/cat-pattern \
  --width 29 --height 29 \
  --classification pixel-art
```

Automatic sizing considers standard 29 × 29, 58 × 29, 29 × 58, and 58 × 58 layouts. Explicit `--width` and `--height` must be paired; layouts over four boards require `--confirm-large-board`.

Do not send an occluded photo directly to the compiler. An Agent first identifies the subject and removes the hand, table, pegboard, and other interference. If reconstruction cannot be verified, it must remain `review-required`. The public example keeps both the raw photo and its cleaned intermediate:

```bash
python plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/create_pattern.py \
  --input examples/intermediates/occluded-finished-beads-clean.png \
  --output-dir work/occluded-pattern \
  --width 58 --height 58 \
  --palette examples/palettes/octopus-generic.json \
  --verification review-required \
  --classification finished-bead-photo \
  --removed-interference hand fingers wooden-table transparent-pegboard pegs glare shadows background
```

## Outputs

- `pattern.json`: canonical grid, palette, counts, board layout, and uncertainty state.
- `template.png`: buildable coordinate grid, five-cell guides, standard-board edges, and legend.
- `colors.csv`: `id,name,name_zh,hex,brand_code,count` with exact counts.
- `report.json`: classification, cleanup, board/palette decisions, warnings, and verification state.
- `review.png`: emitted only when inferred cells or cleanup markers exist.

`total_beads` equals the sum of `color_counts`. A non-empty output directory is refused unless `--force` is explicit.

## Board sizing

The standard module is 29 × 29. Selection balances cropping, unused area, silhouette retention, and bead count. Custom dimensions are allowed but clearly marked as not matching standard boards. Ask before finalizing a design over four boards.

## Generic and brand palettes

Without `--palette`, the compiler uses the bundled 16-color generic JSON palette. You may pass a JSON array with `id`, `name`, `name_zh`, `hex`, and optional `brand_code`, or a CSV with this exact header:

```text
id,name,name_zh,hex,brand_code
```

Only supplied palette colors are used. The default is 8–16 colors with dithering disabled. Brand names and codes must come from you.

## Known limitations

“Count-accurate” means deterministic counts for a fixed input, grid, and palette; it is not a guarantee that an ambiguous photo, an occluded region, or real-world inventory is objectively correct. Empty cells and white beads are distinct, but a bad subject mask still affects output. Review `review.png`, `report.json`, and physical inventory before building. This project does not guarantee ironing, material safety, or finished-work quality.

## Development and tests

```bash
python -m pip install -e ".[test]"
pytest -q
python tools/package_release.py
```

Packaging writes two deterministic archives:

```text
dist/fuse-bead-designer-plugin-v0.1.0.zip
dist/create-fuse-bead-patterns-skill-v0.1.0.zip
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run tests before submitting changes. Public examples must be redistributable; never commit user images, credentials, or private `work/` intermediates.

## License

[MIT](LICENSE) © 2026 MrLQQ。
