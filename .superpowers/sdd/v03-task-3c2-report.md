# Task 3C2 report: CLI exact-grid compilation

## RED / GREEN evidence

The implementation proceeded one end-to-end behavior at a time:

1. The first `68 x 60` explicit exact-grid test failed with
   `total_beads == 0` instead of `3`. The legacy region sampler had ignored
   the sparse occupied center pixels. After routing explicit exact grids
   through `sample_cell_centers` without implicit cleanup, the test passed
   while preserving `68 x 60` dimensions and `3 x 3` board coverage.
2. The unambiguous `16 x 16` logical checkerboard enlarged to `80 x 80`
   initially failed because legacy board selection chose a different grid and
   center-sampling geometry then rejected it. Wiring
   `recover_nearest_neighbor_grid` before `layout_boards` made the recovered
   `16 x 16` grid pass. Ambiguous pattern drafts now return the actionable
   `provide --width and --height` CLI error.
3. The high-resolution draft test initially compiled the original red image
   instead of the black draft. Selecting the draft as the compilation image
   made the output black while retaining source, draft, and compiled paths as
   provenance.
4. Self-review found a compatibility edge case: a high-resolution command
   with `--legacy-resample` compiled the draft (black) rather than the
   original v0.2 input (red). A regression test observed that RED result;
   restricting draft selection to exact routes restored the legacy behavior.

Fresh focused verification:

```text
$ .venv/bin/python -m pytest tests/test_cli.py tests/test_models.py -q
80 passed in 8.05s
```

The full suite was run once after focused verification:

```text
$ .venv/bin/python -m pytest -q
208 passed in 9.49s
```

## Delivered scope

- Exact routes use explicit logical dimensions when supplied, otherwise require
  unambiguous nearest-neighbor recovery.
- Exact dimensions are passed to `layout_boards` without resizing the logical
  pattern.
- Exact center sampling preserves occupied center cells and skips cleanup
  unless `--cleanup` is present.
- Explicit `--sampling median` keeps exact logical dimensions while selecting
  the compatibility sampler.
- `unclassified` and `--legacy-resample` retain original-input
  `select_board` + `sample_cells` + cleanup behavior.
- High-resolution exact routes compile `--draft-input`; the original input is
  retained as provenance.
- Pattern settings and CLI reports record source classification, resolved
  sampling and cleanup, effective grid box, draft use, grid evidence, and
  source/draft/compiled inputs. Existing artifact names, pattern schema
  version, and existing compile-report keys remain intact.

## Self-review

- Only the four Task 3C2 code/test files and this report were changed.
- Parser, policy, recovery, sampler, and layout APIs were consumed without
  modification.
- Optional `CompileReport` provenance fields are emitted only when supplied,
  preserving existing direct report serialization.
- Exact patterns needing more than four physical boards still require
  `--confirm-large-board`; this preserves the existing safety gate.
- Center sampling retains its fixed geometry requirement of at least four
  source pixels per logical cell; failures remain actionable CLI errors.

## Review fixes

Two review findings were corrected with focused regression cycles:

1. Exact `--sampling median` with `--grid-box` initially sampled the full
   padded image. A synthetic black `1 x 1` grid surrounded by red padding
   failed as red instead of black. Exact median sampling now crops both the
   image and occupancy mask to the resolved grid box before calling
   `sample_cells`; the resolved logical dimensions are unchanged, and the
   legacy branch still samples the full original image.
2. High-resolution exact compilation initially accepted both a missing and a
   corrupt original `--input` when the draft was valid. Both parametrized
   cases returned success in RED. The CLI now opens and validates the original
   source independently before opening and compiling the draft, so provenance
   cannot name an unreadable source.

Fresh review-fix verification:

```text
$ .venv/bin/python -m pytest tests/test_cli.py tests/test_models.py -q
83 passed in 9.34s

$ .venv/bin/python -m pytest -q
211 passed in 9.79s
```

Self-review confirmed that the median crop is guarded by `exact_route`, draft
pixels remain the only compiled pixels for a valid high-resolution exact
route, missing/corrupt source failures publish no output directory, and no
parser, policy, recovery, sampler, layout, schema, documentation, version, or
example files changed.
