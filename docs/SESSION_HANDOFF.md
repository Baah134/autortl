# Current AutoRTL checkpoint

Updated October 26, 2026 (America/New_York). Verify files, Git, ownership and
actual jobs before acting. Canonical checkout: Downloads/autortl-work. Preserve
the separate Downloads/autortl copy. User choice: command-line Vivado.

## Published milestone

GitHub main and development were verified at
185dadc119ebf7e8755c7257dc16d3e6576fd087. Local main was fast-forwarded without
checking out or changing working files. All 1,155 committed archive blobs match
three manifests. This is the original 227-file FIR milestone, before the local
verification correction below. The published harness runtime matches be60de7.

- Full regression: 1,429 passed in 558.54 seconds, all 227 identities unchanged.
- Independent FIR admission: control plus 27 compiling behavioral faults, 28/28.
- Generated signed FIR: 78 to 52 LUTs, 66 to 67 FFs, no DSPs; setup -0.327 to
  +0.169 ns, hold +0.106 ns; reported estimated power unchanged at 0.088 W.
- First feasible design used 80 LUTs. Final result used 12 model calls,
  1,190.343 charged tool seconds and 1,429.016 CLI wall seconds.
- Exact saved top and frozen child independently passed 800 cycles. Actual
  DONE reuse succeeded; six restored tamper probes failed as required. All
  454 protected identities, budget, router statistics and file set stayed intact.
- The original run and its 610-file archive are never resumed or regraded after
  runtime changes. This does not prove arbitrary in-flight crash or formal safety.

## Current local work: verification correction; full regression active

Frozen original generated-grader audit measured 18/27 faults detected, nine
missed, zero ungraded. Independent verification detected all 27. That audit is
archived with 287 files before correction; original run/budget/statistics intact.

The correction uses existing mechanisms: six alternating signed boundary
payloads, legal invalid bubbles/noise, and wholly off-edge pulses for synchronous
reset contracts. Producer hold uses the previous rising-edge handshake. Oracle,
schema, roles, budgets and severity/verdict policy are unchanged. Taxonomy and
acceptance criteria were recorded before implementation.

- Signed-only proof: same original generated oracle/reference/truncation fault;
  old fault passed, corrected grader emitted five assertions, both controls
  passed. 104 to 110 payloads; original prefix/random inputs preserved; expected
  range reaches -2169 and 2166. Intermediate 228-file snapshot archived (266 files).
- Driver proof: all five nominal controls passed coverage, including zero-latency,
  busy operation, 16-cycle input blocking, renamed active-low and async reset.
  A deliberately bad producer driver triggered nine monitor errors. Those six
  probes are separate from the RTL fault denominator.
- Full corrected audit: 22/27 detected, five missed, zero ungraded; same old
  oracle/reference/faults and byte-identical signed-only payload/expected arrays.
  No models or synthesis; 415.375 diagnostic wall seconds. Archive has 597 files
  and the exact staged 230-file source. Independent review found no blocker.
- Remaining faults concern occupied reset retention and FIR-specific port values
  during asserted reset. Generic ResetSpec lacks pending flush/preserve policy;
  the independent contract checker continues to cover these properties.
- Pure staged focus: 117 passed in 6.83 seconds; original four failed/six passed
  preserved. Signed-only focus 107 passed; its original seven/four retained.

Canonical source now exactly matches the vendor-tested 230-file stage. Only
autortl/tbgen.py and data/taxonomy.yaml differ in the runtime implementation;
three new test/helper files and a fixture README correction are also local.
No further source, test or fixture edits during frozen experiments.

Full regression 56345 completed: **1450 passed in 457.63 seconds**.
All 230 identities stayed unchanged. Archive: evidence/2026-10-26/
fir4-coverage-tests-01. No test/vendor/model job currently active. The tested
runtime is ready for development publication and fresh FPGA gates. Source stays
frozen; do not edit it during fresh build02 or campaign13.

Temporary system-awake helper: 96281, watching work/fir4-coverage-awake.flag,
bounded 120 minutes since about 09:41. Previous 6908 released and completed.
Remove the current flag and verify helper exit when the queue ends; no permanent
power settings changed.

## Exact next actions

1. Finish 56345; inspect fir4-coverage-full-result-01.json. If passing, run
   work/archive_fir4_coverage_tests01.py; preserve any failure before edits.
2. Publish the reviewed tested runtime to development. Verify exact source230
   and committed archive blobs. Main remains the completed original milestone
   until the changed runtime's remaining gates pass.
3. Launch work/run_signed_fir4_build02.py in a fresh output directory. Same
   admitted spec/TB; N=1, at most 3 iterations, 16 calls, 25 tool / 35 wall minutes,
   one infrastructure retry, no qualification-reference seed. Do not modify or
   resume original01 under this runtime. Preserve all new outcomes and costs.
4. On actual DONE, independently verify exact winner/child and restored probes,
   then archive02 BEFORE another model job (router record slicing is bound).
5. Run work/run_campaign13.py: fresh FULL tier0 runtime gate, original budgets.
   This is a required regression, not a new counter design objective. No higher
   tier is held. Archive actual history/cohort and source verification.
6. Integrate main only after these gates; verify remote heads and committed
   manifest blob bytes. Update README from actual results and refresh shared
   memory. Release temporary awake request when the owned queue ends.

## Evidence and ownership

Workspace: C:/Users/prince.baah/Documents/Codex/2026-10-15/hey. Helpers in work/;
raw outputs in outputs/. Canonical evidence/2026-10-26 contains generated FIR01,
original generated-grader audit, signed-boundary comparison and driver comparison.
Independent admission remains evidence/2026-10-25/signed-fir4-admission-attempt-01.
Git and PROGRESS preserve prior FIFO/divider/dot-product milestones.

Coordinator: Codex / signed FIR4 Oct26, eight-hour lease. Root owns canonical
fixture, notes/evidence and signed-scoreboard-corners scopes. Isolated stages:
fir4-signed-corners-stage and fir4-driver-stage; do not rewrite their frozen proof.
One coordinator and one vendor queue. No automatic scheduling/provider failover.

Target: xc7a35tcpg236-1, 100 MHz, ideal zero min/max I/O; no board deployment.
Prior runtime gate was campaign12, 2/2, new-cohort streak one, held false.
No controlled weak-model or product-superiority claim is made.
