[中文](README.md)

# Fuse Bead Designer

Send a finished-bead photo, object photo, or high-resolution illustration to an Agent and receive a buildable grid, per-color quantities, and a reviewable report. The Agent identifies and cleans the subject; a deterministic compiler derives the grid and counts from the same `pattern.json` instead of guessing from a rendered image.

![Modern fuse-bead template](plugins/fuse-bead-designer/assets/screenshot-template.png)

## First use: send this sentence to your Agent

> Please install this Codex plugin: https://github.com/MrLQQ/fuse-bead-designer. Complete the installation yourself; after it succeeds, stop. Do not run examples or install additional runtime dependencies; only remind me to start a new task.

Installation changes the local environment, so the Agent asks for permission once. After approval, the Agent checks and completes installation internally; you do not need to copy terminal commands. It stops after installation; start a new task and then send the image request below.

## Everyday use: upload an image and describe the result

Attach the source image in an image-capable Agent conversation, then send:

> Turn the attached image into a fuse-bead pattern

You can add natural constraints such as “prefer standard 29 × 29 boards,” “preserve white beads,” or “do not guess behind this occlusion; mark it for my review.” The normal flow does not expose a Skill token or require local commands.

## From source image to buildable pattern

All four rows below use real repository inputs and deterministic compiler output. They are not illustrative mockups.

<table>
  <tr>
    <th>Scenario</th>
    <th>Source</th>
    <th>Fuse-bead template</th>
    <th>Result</th>
  </tr>
  <tr>
    <td><strong>Occluded finished beads</strong><br>Fingers, board, and scene interference</td>
    <td><img src="examples/inputs/occluded-finished-beads.png" alt="Occluded finished-bead source" width="260"></td>
    <td><img src="examples/outputs/occluded-finished-beads/template.png" alt="Occluded finished-bead template" width="360"></td>
    <td>58 × 58<br>1,525 beads<br><code>review-required</code></td>
  </tr>
  <tr>
    <td><strong>Occluded high-resolution image</strong><br>A label hides part of the subject</td>
    <td><img src="examples/inputs/occluded-high-resolution-image.png" alt="Occluded high-resolution source" width="260"></td>
    <td><img src="examples/outputs/occluded-high-resolution-image/template.png" alt="Occluded high-resolution template" width="360"></td>
    <td>58 × 58<br>719 beads<br><code>review-required</code></td>
  </tr>
  <tr>
    <td><strong>Actual object photo</strong><br>Subject extracted from a studio background</td>
    <td><img src="examples/inputs/actual-object-photo.png" alt="Actual object source photo" width="260"></td>
    <td><img src="examples/outputs/actual-object-photo/template.png" alt="Actual object fuse-bead template" width="360"></td>
    <td>58 × 29<br>501 beads<br><code>verified</code></td>
  </tr>
  <tr>
    <td><strong>High-resolution non-pixel illustration</strong><br>Continuous color reduced to a discrete grid</td>
    <td><img src="examples/inputs/high-resolution-mascot.png" alt="High-resolution non-pixel source" width="260"></td>
    <td><img src="examples/outputs/high-resolution-mascot/template.png" alt="High-resolution mascot fuse-bead template" width="360"></td>
    <td>58 × 58<br>1,234 beads<br><code>verified</code></td>
  </tr>
</table>

## What you receive

Each generation delivers:

- `template.png`: buildable coordinates, five-cell guides, standard-board boundaries, and a modern quantity legend.
- `colors.csv`: colors actually used, hex values, optional supplied brand codes, and exact counts.
- `pattern.json`: the canonical grid, palette, board layout, and per-color counts.
- `report.json`: input classification, cleanup record, sizing decision, warnings, and verification state.
- `review.png`: focused uncertainty markers when cleanup or inferred regions need review.

Verification states are operational:

- `verified`: no semantic reconstruction affected the subject; counts belong to the confirmed design.
- `inferred-low`: only limited, explainable reconstruction was used; inspect the markers.
- `review-required`: a key region remains uncertain. Counts are provisional; inspect `review.png` and `report.json` before buying beads or building.

“Exact counts” means deterministic totals for a fixed input, grid, and palette. It is not a claim that an ambiguous photo, unknown occlusion, or physical inventory is objectively correct.

## Supported sources and automatic decisions

The Skill handles general inputs, not only pre-pixelated art:

- Finished-bead photos: distinguish the bead subject from fingers, tables, transparent boards, glare, and shadows.
- Occluded photos or illustrations: reconstruct only explainable regions; unresolved key content stays review-required.
- Actual object photos: isolate the subject from its photographic background while preserving subject details such as white areas.
- High-resolution non-pixel images: simplify contours and continuous colors so one cell maps to one bead.
- Clean pixel art: preserve proportions and hard edges where possible.

The standard module is 29 × 29. The Agent chooses common combinations such as 29 × 29, 58 × 29, 29 × 58, or 58 × 58 from the subject proportions, or follows a natural-language request for a custom size. It asks before exceeding four boards. The default palette is generic and never invents brand codes; `brand_code` is retained only when you supply a brand palette.

## Codex and other Agent hosts

Codex installs the full Plugin where possible. Other [Agent Skills](https://agentskills.io/)-compatible tools can install the standalone Skill from the Release. Installation locations, permission models, image understanding, and image editing capabilities vary by host, so the same natural-language request can trigger different internal steps.

For normal users, the boundary remains the same: send the installation prompt and an image request. The Agent obtains installation permission and performs supported installation itself. If the host lacks a required image capability, it should explain the limitation and ask for a better source instead of inventing subject detail or hidden regions.

## Developer

> The commands below are only for Agent implementers, maintainers, and developers debugging the compiler. Normal users should not run them; use the natural-language workflow above.

### Codex Marketplace / Plugin

Install the fixed v0.2.0 release:

```bash
codex plugin marketplace add MrLQQ/fuse-bead-designer --ref v0.2.0
codex plugin add fuse-bead-designer@fuse-bead-designer
```

Debug from a local clone:

```bash
git clone https://github.com/MrLQQ/fuse-bead-designer.git
cd fuse-bead-designer
codex plugin marketplace add "$PWD"
codex plugin add fuse-bead-designer@fuse-bead-designer
```

### Standalone Skill

```bash
cp -R plugins/fuse-bead-designer/skills/create-fuse-bead-patterns \
  "${CODEX_HOME:-$HOME/.codex}/skills/"
```

### Local development, tests, and packaging

```bash
python -m pip install -e ".[test]"
pytest -q
python tools/package_release.py
```

v0.2.0 packaging writes:

```text
dist/fuse-bead-designer-plugin-v0.2.0.zip
dist/create-fuse-bead-patterns-skill-v0.2.0.zip
```

### Direct deterministic compiler use

The Agent normally calls the compiler internally. Run it directly only for debugging:

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

Explicit sizing requires both width and height. More than four boards requires explicit confirmation. The compiler refuses a non-empty output directory unless a developer deliberately uses its force option. Custom palettes may be JSON entries with `id`, `name`, `name_zh`, `hex`, and optional `brand_code`, or a CSV with the exact header `id,name,name_zh,hex,brand_code`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Public examples must be redistributable. Never commit user images, credentials, or private intermediates from `work/`.

## License

[MIT](LICENSE) © 2026 MrLQQ.
