# Task 8: Portable Compiler CLI

## RED

`tests/test_cli.py` was added before the CLI implementation. The worktree's
default virtual environment initially lacked both Pillow and pytest, and a
plain offline `uv run --extra test` could not resolve its cache. That was an
environment failure, not evidence about the absent CLI.

Using the established offline Python 3.12 runtime with bundled Pillow and the
provided pytest path, the first behavioral run exercised the new contract and
found one test-order defect: the output-guard assertion ran after the forced
write. The test was corrected to assert refusal before running `--force`.

## GREEN

Focused CLI verification:

```text
15 passed in 2.09s
```

Full compiler suite, Python 3.12.13 with Pillow 12.2 and pytest 8.3.5:

```text
119 passed in 3.95s
```

The same final command also passed `py_compile` for the portable entry point
and all compiler modules, followed by `git diff --check`.

## Files

- `scripts/create_pattern.py`: CWD-independent executable wrapper.
- `scripts/fuse_bead_designer/cli.py`: argparse contract, validation, image
  loading, masking, board selection, sampling, cleanup, report assembly, and
  artifact writing.
- `tests/test_cli.py`: subprocess coverage for portable execution, automatic
  and explicit board selection, option/user-error handling, palette fidelity,
  review output, force safety, and count agreement.

## Self-review

- All user-input failures use argparse's deterministic exit code `2` without
  a traceback.
- Width and height are paired; color limits are exactly 8 through 16;
  coordinates use `column,row` and are bounds-checked after board selection.
- More than four standard-board modules requires explicit confirmation.
- A non-empty directory is rejected without `--force`; forced writes only use
  the established generated-artifact writer and preserve unrelated files.
- The CLI never manufactures palette names or brand codes: supplied palette
  metadata is serialized unchanged.

## SHA-256

```text
0718278a92a253a0cef69b5b3c9dbee2c8199677d1f114bb3e5cd98337d81152  cli.py
13a38c8ac9b7c24fb05e6a16c24e00ec46f76c15d2cd7370eadb8e0317de71de  create_pattern.py
f19bf60367253b4224e16cdcb7fd72dd341b9d5d75c950e00f28613209327707  test_cli.py
```

## Corrective review follow-up

### RED

The review regressions exposed three end-to-end contract gaps: `--force` could
write JSON/CSV before failing on an existing generated-artifact directory,
`report.json` omitted inferred regions, and a `.csv` palette was incorrectly
parsed as JSON. The focused regression run reported `10 failed, 34 passed`.

### GREEN

Focused CLI, artifact, report, and palette verification:

```text
44 passed in 4.07s
```

Full compiler verification on the established Python 3.12.13 runtime:

```text
127 passed in 7.16s
```

`py_compile` for the CLI/compiler modules and `git diff --check` also passed.

### Corrections and self-review

- Artifact generation now renders and serializes into a same-filesystem staging
  directory. Generated target conflicts (including directories and symlinks)
  are rejected before writing; publish temporarily backs up only the known
  generated artifacts and restores them on publish failure. Unrelated files
  are never moved or deleted.
- `CompileReport` now serializes `inferred_cells`; the writer requires report
  coordinates to be list-shaped, integer, in-bounds, and equal to the
  canonical pattern coordinates before creating output.
- Custom palette loading selects JSON or CSV by extension. CSV requires the
  exact UTF-8/UTF-8-sig header `id,name,name_zh,hex,brand_code`, rejects extra
  or short rows deterministically, and reuses the existing palette/brand
  validation without manufacturing metadata.

### Corrective SHA-256

```text
cac6615e77f2d96f2875b1f1ca02042b079149df0ff5887fdcf6f10f47380897  cli.py
31bb644d3a32e14b2fc3852538baab366436aac13cfeb8203a4b6bc40921b0d6  io.py
8f3749aeefb1d12d0565fea73c9c3d2750c5c38f9fcd87a204c67e75d11c248c  models.py
e4da36ad80c69bcb275cc85e1b504ad59f88233fe224115dc15c91ae19d7c78a  palettes.py
d08fbcdddf4db8394899b8af992b25a3898df550fa2ed6080c80af97146c1d8b  test_cli.py
5cbff2a70f85753fc970d51254944d0a320cbc7af00cb98a7ece23dfee449559  test_render.py
b0ec71762c7d4b85286c331a61ed54ce4925083b1409aeabd62aa80a0648cdf0  test_palettes.py
```
