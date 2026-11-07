# Gate source-identity traversal: integration-ready review

Only `tools/tier0_gate.py` and new
`tools/tests/test_gate_identity_traversal.py` are proposed for integration.
Apply `proposal-v2.patch`, not the earlier one-file proposal. Canonical helper
SHA-256 remained `bf9439bcd641abf017af93c3ce24d613e963eb8ab49702e3bf469f2020b48d44`
through validation. No canonical file, Git index, running job, model, Vivado,
serial interface or board was changed/accessed.

The minimal implementation replaces `Path.rglob` with top-down
`os.walk(..., followlinks=False)` and removes exactly the `worktrees` directory
from the first `.claude` directory's descent list. It does not add cache pruning,
change suffixes/roots or normalize source bytes. The returned dictionary remains
sorted. Worktrees elsewhere, similarly named directories and skills stay included.

The test has a small self-contained historical selector. It no longer imports
the stage's saved historical helper. The unchanged test file gives:

- Original helper: **1 failed, 4 passed, 1 skipped in 0.82s**. Only the
  observed-excluded-traversal regression fails.
- Proposed helper: **5 passed, 1 skipped in 0.70s**.
- Synthetic traversal probe: old **28 total / 8 excluded-subtree scandir calls**;
  proposed **12 total / 0 excluded-subtree calls**, with identical full path/hash
  dictionaries. This proves pruning for this fixture; it is not a live-tree
  wall-time measurement.

Exact dictionary comparisons cover raw CRLF bytes, missing selected roots,
similarly named directories, nested retained `worktrees`, a real Windows
directory junction and a real selected-root junction. The native junction tests
ran successfully outside the restricted sandbox. The initial restricted run's
two junction permission failures are retained in `v2-after-tests.txt` rather
than relabeled as design regressions.

The available interpreter is CPython 3.12.14. Its local `pathlib.py` implements
recursive glob traversal using `Path.walk(follow_symlinks=False)`; a file symlink
is still eligible through `Path.is_file`, and directory symlinks are not descended.
`os.walk(followlinks=False)` has the same selected-file behavior. Junctions are
not ordinary symbolic links on this runtime: both algorithms descend them,
as the real junction comparisons verify. The explicit file/directory symlink
test could not run because Windows denied symbolic-link privilege (1314),
including outside the sandbox. It is retained to run when available, and skips
only OS privilege/access failures. No actual symbolic-link equality result is
claimed on this host. Cross-version equality is guarded by the same legacy
comparison tests, not inferred from the API names.

`receipt-v2.json` records command lines, exits, source/test/patch/log hashes and
the probe counts; `v2-scandir-observation.json` retains the complete dictionaries.
`validate_v2.py` reproduces the before/after run in this isolated stage, always
restoring proposed staged code in a finally block. Parent owns canonical
integration and full tooling validation after confirming the old invocation has
ended; these are focused selection tests only.
