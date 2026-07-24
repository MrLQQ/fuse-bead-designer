# Fuse Bead Designer v0.3 Pattern-First Design

## Goal

Make the plugin reproduce the successful source-to-pattern workflow: an Agent
may use image understanding to design or restore a bead-friendly logical
pattern, while deterministic code owns grid normalization, palette mapping,
counting, board tiling, and final rendering.

The design must prevent both observed failure modes:

- forcing a detailed subject into a small standard-board grid and losing its
  identity;
- treating display pixels as beads and inflating a visually similar design to
  several times the necessary bead count.

## Product contract

Installation and use are separate tasks.

The README's first-use prompt is:

> 请安装这个 Codex 插件：https://github.com/MrLQQ/fuse-bead-designer 。请由你完成安装；安装成功后停止，不要运行示例或安装额外运行依赖，只提醒我新建任务。

The repository installation contract must stop after confirming the plugin is
installed and instructing the user to start a new task. An installation request
does not authorize cloning the repository, compiling an example, creating a
virtual environment, or installing Pillow.

In a new task, the user only needs to attach an image and ask for a fuse-bead
pattern in natural language.

## Architectural principles

### Pattern first, boards second

`pattern_width` and `pattern_height` describe the art's logical bead grid. They
may be any positive integers. `board_columns` and `board_rows` are derived later
with `ceil(pattern_dimension / 29)`.

Standard 29-cell boards are manufacturing metadata, not image resampling
targets. Automatic pattern-size recommendations must not be restricted to
multiples of 29 or to four boards.

### Source class changes the workflow

The original source is classified as one of:

- `finished-bead-photo`
- `pixel-art`
- `high-resolution-image`

The deterministic compiler additionally accepts a `pattern-draft`, which is the
plain grid-aligned intermediate produced after restoration or semantic design.

Each route has a distinct contract:

| Source | Required preparation | Deterministic behavior |
|---|---|---|
| Finished bead photo | rectify perspective; remove fingers, glare, board holes, and background; preserve visible bead placement; mark inferred occlusion | receive a declared rectified logical grid; center-sample cells; no singleton cleanup |
| Pixel art | preserve logical pixels and intentional empty cells | recover a nearest-neighbor scale only when evidence is unambiguous, otherwise require declared dimensions; center sampling; no singleton cleanup |
| High-resolution image | create a plain bead-pattern draft that prioritizes silhouette and identity features | normalize the declared draft grid; map palette; count cells; no model-generated legend or quantities |
| Pattern draft | provide grid dimensions and optional grid bounds | compile exactly that grid; never choose a standard board size first |

If a finished-bead photo has not been rectified into a declared grid, a
high-resolution image has not yet been converted into a pattern draft, or
pixel-grid recovery is mathematically ambiguous, the compiler must fail with an
actionable message instead of silently applying generic rectangular
downsampling.

### AI and deterministic responsibility boundary

Image generation/editing may:

- isolate and rectify a subject;
- conservatively restore an occluded region;
- create the semantic bead-pattern draft;
- choose which details should survive simplification.

It must not:

- invent color counts;
- draw the final color legend or coordinates;
- be treated as authoritative for grid dimensions;
- report a design as verified when cells were inferred.

Deterministic code must:

- preserve declared logical empty cells and use an explicit grid box for display
  padding;
- normalize the exact logical cell matrix;
- map each occupied cell to the selected palette;
- count every color;
- derive board layout after pattern dimensions are fixed;
- render `template.png`, `colors.csv`, `pattern.json`, `report.json`, and
  `review.png`.

## Compiler interfaces

### Route policy

Add a route-policy module with:

```python
@dataclass(frozen=True)
class RoutePolicy:
    classification: str
    requires_pattern_draft: bool
    sampling: str
    cleanup: bool
    crop_subject: bool

def policy_for(classification: str) -> RoutePolicy:
    ...
```

`pixel-art` and `pattern-draft` use center/nearest sampling and disable cleanup.
`high-resolution-image` requires a pattern draft. `finished-bead-photo`
requires a pattern draft unless the caller explicitly declares that the input
has already been rectified into a clean logical grid.

Nearest-neighbor logical-grid recovery is confidence-gated. A uniform image,
anti-aliased image, or raster with multiple equally valid logical scales must
raise an ambiguity error. Explicit logical dimensions always win.

Raster scale is not uniquely identifiable in general: a composite scale such as
`4x` can also be represented as `2x` with repeated logical cells. Automatic
recovery therefore succeeds only when exactly one nontrivial integer scale
passes byte-for-byte downsample/re-expansion validation. Normal Agent workflows
should provide verified logical dimensions; recovery is a conservative
convenience, not an authority.

### Pattern sizing and board layout

Replace board-first selection with two operations:

```python
def recommend_pattern_sizes(
    subject_width: int,
    subject_height: int,
    detail_score: float,
) -> tuple[PatternSizeCandidate, ...]:
    ...

def layout_boards(width: int, height: int, module_size: int = 29) -> BoardLayout:
    ...
```

Recommendations preserve aspect ratio and produce arbitrary logical dimensions
for economy, balanced, and detail variants. They are advisory. Explicit pattern
dimensions always win.

The detail score must be measured from the relevant subject/grid box rather than
remaining the current fixed `0.5`.

Rendering must draw board seams at every 29 cells even when the last board is
partial. A `68 x 60` pattern therefore remains `68 x 60` while showing seams at
29 and 58 in both applicable directions.

### Exact-grid compilation

The CLI keeps `--width` and `--height` as logical pattern dimensions and adds:

- `pattern-draft` to `--classification`;
- `--grid-box LEFT,TOP,RIGHT,BOTTOM` for a draft whose grid does not fill the
  image;
- `--draft-input PATH` for the semantic draft created from a high-resolution
  source;
- `--rectified-grid` to allow direct finished-bead compilation;
- `--cleanup` as an explicit opt-in compatibility switch.

Default compilation for `pixel-art` and `pattern-draft`:

1. preserve the declared logical canvas; use `--grid-box` to exclude display
   padding;
2. divide only the declared grid box into the declared logical cells;
3. sample a small center window, not the full rectangle median;
4. map to the palette;
5. do not remove isolated cells;
6. derive board layout from the resulting pattern.

The old region-median path remains available only as explicit compatibility
behavior. It is not the default natural-language workflow.

## Agent workflow

The Skill must use the following sequence:

1. inspect the source at full resolution;
2. classify the original source;
3. identify obstructions and uncertainty;
4. choose the appropriate restoration/design route;
5. create a plain pattern draft when required;
6. determine or verify the draft's actual grid instead of trusting a requested
   image-model dimension;
7. compile the exact grid deterministically;
8. compare the template with the source/draft before delivery;
9. report inferred regions and practical board layout.

For a high-resolution source, the Agent should target a bead budget and identity
preservation, not a standard board dimension. It may compare economy, balanced,
and detail variants, but should recommend one without forcing the user through
unnecessary questions.

## Quality gates

The regression suite must prove:

- installation prompts stop after installation;
- classification changes route policy and invalid routes fail loudly;
- a non-29-multiple grid such as `68 x 60` remains `68 x 60`;
- `68 x 60` derives a `3 x 3` board layout without resizing the art;
- an explicit grid box excludes display padding without deleting intentional
  empty logical cells;
- ambiguous logical pixel scales fail with an actionable error;
- center sampling preserves intentional single-cell features;
- pixel-art and pattern-draft routes do not run singleton cleanup;
- totals equal the sum of color counts;
- the Skill tells the Agent to create a semantic draft but never lets the image
  model count beads or draw the final legend.

Add one redistributable complex regression fixture with small eyes, highlights,
ornaments, thin edges, and dark neighboring colors. The regression must assert
feature-cell preservation and a bead-count band rather than one overfitted
exact picture.

## Compatibility and release

- Release as `0.3.0`.
- Keep the existing artifact formats compatible.
- Preserve the old median sampler behind an explicit compatibility option.
- Do not claim automatic glare/perspective bead-lattice detection in this
  Pillow-only release; rectified finished-bead inputs require declared grid
  evidence.
- Update Chinese README first and keep the English README equivalent.
- Rebuild both release archives deterministically.
- Validate the Skill and Plugin before publishing.
