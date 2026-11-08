# Independent benchmark artifact review — November 8, 2026

Status: approved after three scoped corrections; no remaining blocker in this
artifact-only implementation. Parent retains canonical integration/publication
and the active AES04 boundary.

Scope: workspace-only `work/nov8-benchmark-artifact-stage`, against the recorded
acceptance and bounded implementation review. No canonical edits, model calls,
vendor/simulator/hardware actions, task selection, installation or network use.

Initial reviewed implementation SHA-256:
`9db201b6f718dc62e3e678267d9725f32c3be31648474cff71d519ed768f1cff`.
Its original receipt recorded 69 passed and two native Windows permission
skips, with all four tested inputs unchanged. The author preserved that V1
source/log/receipt separately under `review-v1/`; it is not the final result.

## Final reviewed identities and validation

| File | SHA-256 |
|---|---|
| benchmark/artifacts.py | `94fabd8db8c01e6170f74ed3bf1ca25dbd03c031d7b6fe69586979af155f5d2e` |
| benchmark/__init__.py | `d1c4b40e83bd049b3b95bd56c4d276dbf2d0fcf5d3b0e28cd47bdc2db33dbef9` |
| tests/test_benchmark_artifacts.py | `b811c2dac062164b2a71f4c5f12eceb5b5ef0338f5e3ba46b032963a5d87aa91` |
| docs/BENCHMARK_ARTIFACTS.md | `b3490233844a34fd3c858e0e7014759fb9077fb4f88bef8492bba49144f1c1f3` |
| proposal.patch | `5e4cbe2dec75e5f393737a8695b5e5e0ac7555cb4932191fbeb9e2725712a3a0` |
| receipt.json | `e4a1f31aec67c952db712388cce83e7e5bf3e5202195fb3832b4d445d7ebf4cd` |

Recomputed all six raw hashes. Inspected final source and the six added test
cases. Final author receipt/log record **75 passed, 2 skipped in 9.73 seconds**,
exit zero, all four tested inputs unchanged. Native symlink and junction
creation were denied by Windows permissions; neither is counted as passing.

Independently reran the original failure probes against the revised module,
without mirroring its full suite: ordinary UTF-8 remains accepted; UTF-16 and
UTF-32 now raise `ArtifactError`; the huge integer budget raises `ArtifactError`
under the documented finite machine-time contract; the actual extra file in
a synthetically unreadable subtree now blocks loading. The postfix runner
asserts these outcomes and exits zero. Evidence:
`work/nov8_benchmark_review_postfix.py`,
`work/nov8-benchmark-postfix-probes.json`,
`work/nov8-benchmark-review-probes-fixed/results.json`, and
`work/nov8-benchmark-inventory-probe-fixed/result.json`.

## Reproduced findings

1. JSON bytes were passed directly to `json.loads`, which autodetects UTF-16
   and UTF-32. Both encodings were accepted despite the UTF-8 contract.
   Require strict UTF-8 decoding before JSON parsing and explicit BOM policy.
2. `math.isfinite(10**400)` raised an uncaught `OverflowError` for integer
   tool-seconds input. State a numeric contract and report unsupported values
   as `ArtifactError`, rather than leaking a conversion exception.
3. `os.walk` without `onerror` silently ignored an unreadable extra subtree.
   With an actual unlisted `extra.py` and a scoped synthetic scandir denial,
   loading accepted the original expected ID. Fail closed on traversal errors.

Probes retained in `work/nov8_benchmark_review_probe.py`,
`work/nov8-benchmark-review-probes/results.json`,
`work/nov8_benchmark_inventory_probe.py` and
`work/nov8-benchmark-inventory-probe/result.json`.

All three findings are resolved: strict UTF-8 without BOM is explicit;
nonrepresentable time values fail with a contract error; traversal errors
propagate and fail closed. Documentation now explicitly limits the full
public/private loader to the trusted coordinator and supplies generation only
the exported public artifact.

## Final design assessment

The mandatory externally retained artifact ID correctly closes coherent file
plus receipt replacement. Strict declared arm/policy/budget consistency is
appropriate; it is clearly distinguished from actual execution enforcement.
Public receipts are reconstructed from allowlisted fields, and explicit RTL
copying does not discover or repair candidates. Rejected complete and missing
records remain separate. Atomic receipt-last publication, byte checks, no
overwrite, portable path checks and reparse rejection are scoped sensibly.

Completeness/elaboration, candidate selection, semantic RTL safety, global cell
reservation, grading, actual denied-access controls, model accounting and real
benchmark registration remain outside this artifact slice. Native link/junction
controls were skipped for permission limits, not counted as passing. This is
provenance validation under trusted exclusive ownership, not an OS sandbox or
signature system.
