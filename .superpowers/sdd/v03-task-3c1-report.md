# Task 3C1 report: CLI route validation

## RED / GREEN evidence

Each new route behavior was introduced with a focused CLI test before its
minimal parser or validation change. The RED failures were the expected missing
behavior: high-resolution input returned success without a draft; the new
`--rectified-grid`, `--draft-input`, `pattern-draft`, `--grid-box`,
`--sampling`, `--cleanup`, and `--legacy-resample` arguments were initially
unrecognized.

The focused suite is green:

```text
$ .venv/bin/python -m pytest tests/test_cli.py -q
27 passed in 6.81s
```

The full suite is green:

```text
$ .venv/bin/python -m pytest -q
203 passed in 7.60s
```

## Delivered scope

- Added `pattern-draft` and all requested route arguments.
- Calls `policy_for()` immediately after paired-dimension validation, passing
  draft, rectification, and compatibility inputs.
- Rejects missing high-resolution drafts and unrectified finished-bead photos
  before compilation.
- Parses and image-bounds-validates `--grid-box` with clear errors for
  nonpositive and out-of-bounds boxes.
- Resolves sampling and cleanup policy values, records them in pattern settings,
  and lets explicit sampling/cleanup plus `--legacy-resample` select the
  intended policy values.

## Boundary review

This task deliberately does not wire the resolved arguments into exact-grid
sampling, logical-grid recovery, draft-image selection, or board layout. The
current legacy compilation calls remain intact; Task 3C2 will consume the
validated arguments for that branch.
