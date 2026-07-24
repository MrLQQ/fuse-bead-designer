# Task 7: Render and Write All Derived Artifacts

## Provenance

- Renderer font: `NotoSansCJKsc-Regular.otf`, downloaded from
  `https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf`.
- License: the exact `Sans/LICENSE` file from
  `https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/LICENSE`,
  stored as `assets/fonts/OFL.txt`.
- Upstream repository, filename, and SIL Open Font License 1.1 are recorded in
  `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/CONTRIBUTING.md`.

## RED evidence

`tests/test_render.py` was added before either renderer/writer production
module. The focused offline test command failed during collection with the
expected error:

```text
ModuleNotFoundError: No module named 'fuse_bead_designer.io'
```

## GREEN evidence

Focused verification:

```sh
PYTHONPATH=/Users/bytedance/Library/Python/3.9/lib/python/site-packages /Users/bytedance/.local/bin/uv run --offline --no-project --python /Users/bytedance/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 --with jsonschema==4.25.1 python -m pytest tests/test_render.py tests/test_models.py -v
```

Result: `54 passed in 0.50s`.

Full verification:

```sh
PYTHONPATH=/Users/bytedance/Library/Python/3.9/lib/python/site-packages /Users/bytedance/.local/bin/uv run --offline --no-project --python /Users/bytedance/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 --with jsonschema==4.25.1 python -m pytest -v
```

Result: `98 passed in 0.55s`. The bundled Python 3.12 `py_compile` check for
`render.py` and `io.py`, plus `git diff --check`, also passed.

## Self-review

- `template.png` reads cell colors and quantities only from validated
  `Pattern.cells`; labels, bilingual legend entries, quantities, total beads,
  and board count are derived from that same pattern.
- Each cell has a grid line, five-cell lines are stronger, and 29-cell
  boundaries render only when the pattern has a standard board layout.
- `pattern.json` and `report.json` use UTF-8 with `ensure_ascii=False`.
  `colors.csv` has exactly `id,name,name_zh,hex,brand_code,count` in that
  order, and counts agree with `Pattern.total_beads`.
- `review.png` is emitted only if inferred cells or cleanup changes are
  present; orange and cyan outlines identify those two review sources.
- The bundled Noto CJK font is loaded explicitly, avoiding host-font and
  missing-glyph variation.

## SHA-256

```text
3fbf44bb9209e7cc6d61ceaebb26e67b9500195745171a704dcf507efa17a105  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/render.py
0591882b4bc372aa1c5b12466d60aa8ad0d13760fdb3cbd027c6e0dcf47249fd  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/fuse_bead_designer/io.py
2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/assets/fonts/NotoSansCJKsc-Regular.otf
6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/assets/fonts/OFL.txt
1a544f262d7a4015f681e5ce2d1b102659f23ce71865724a164e97092bb2dce1  plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/CONTRIBUTING.md
7e01fbbdc8da47951469a779ffad7db036cc1d2c7708e4f84b46052955d52d0d  tests/test_render.py
```

## Commit

`feat: render count-accurate bead templates`
