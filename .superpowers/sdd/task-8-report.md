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
