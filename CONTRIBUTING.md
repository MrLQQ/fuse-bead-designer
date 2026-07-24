# Contributing

Thank you for improving Fuse Bead Designer.

## Scope and evidence

Keep the semantic image-understanding stage separate from deterministic compilation. Do not describe an inferred area, a brand color code, or a bead count as confirmed without the corresponding source artifact. `pattern.json` is the canonical output; `template.png`, `colors.csv`, and `report.json` must agree with it.

Preserve the pattern-first contract in public documentation and code: route finished-bead photos, pixel art/existing patterns, and high-resolution sources explicitly; fix logical dimensions before deriving board layout; and keep inferred regions visibly provisional. Do not claim that the compiler detects a general bead lattice in ordinary photos.

## Development

Use Python 3.10 or newer, then install and check the project:

```bash
python -m pip install -e ".[test]"
pytest -q
python tools/package_release.py
```

The repository contract test covers the marketplace path, synchronized release versions, public README wording, and public examples. For a release, keep `pyproject.toml`, plugin and marketplace manifests, packaging code, installation instructions, and archive names on the same version. The packaging script emits deterministic archives under `dist/`; do not commit those generated files.

## Tests and examples

Add a focused regression test for every behavior change. Public fixtures must be original or openly redistributable, and their provenance/prompt belongs in `examples/prompts/`. Never add user attachments, credentials, private work directories, or generated content whose license is unclear.

When changing an example, regenerate every artifact with the real compiler and check that `total_beads` equals the sum of `color_counts`.

## Pull requests

Explain the user-visible change, uncertainty behavior, and verification command. Keep the Chinese and English README facts aligned. Changes to a bundled font must retain its upstream license files.
