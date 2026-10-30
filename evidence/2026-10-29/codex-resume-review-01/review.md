# AutoRTL review — October 29, 2026

Reviewed development commit: `749d6d19a7fa03b7ee9db59d3ec0efbc2613a624`.
Comparison point: `da16b6248551293dc246e8ee12f78949430736be` (last Codex change).
Remote development matched the reviewed revision; remote main was `0939c4368e964ae87c9ab0aa85fe5b37185f085c` when checked.

Claude's coordinator lease and processes were active. This review made no edits,
commits, lease changes, model calls, EDA runs, board programming or mailbox posts
in the canonical checkout. Tests and reproductions used a Git archive in this
workspace. Reports concern that fixed revision, not subsequent changes.

## Assessment

The project has made substantial progress toward a strong FPGA/EDA portfolio.
The physical hardware evidence, independently checked host models, replayable
bitstreams, CI, source audit, offline demonstration and code walkthrough materially
strengthen it. It is no longer limited to standalone simulated designs.

The next priority is integration and acceptance correctness. The reviewed commit
still contains several reproducible gaps, and its documentation counts a sandbox
hardening branch as merged when its implementation and tests are absent. Resolve
these before a large comparative benchmark or a claim of fully hardened execution.

## Findings, ordered by priority

### P1 — Claimed golden sandbox hardening is not integrated

`docs/SESSION_HANDOFF.md:9-17` says the hardened identity includes the golden
copy/slice/decorator/timeout corrections. `README.md:42` advertises 1,742 tests.
However, the reviewed commit still has the earlier `autortl/golden.py` and
`autortl/golden_worker.py`. Branch `golden-hardening` at `d71c49c` contains changes
to both files, FSM changes and the new `tests/test_golden_hardening.py`; it is not
an ancestor of the reviewed commit. The new test file is absent at the reviewed
revision. Independent collection reports **1,654 tests** under `tests/`.

Integrate the reviewed sandbox work, or accurately label it pending. Then freeze
the actual combined source and regenerate regression/gate evidence. A commit
message or a subagent test receipt cannot establish integration.

### P1 — Forbidden RTL tasks can evade the new safety filter

`autortl/static_checks.py:36` calls `strip_comments()` before string masking.
The comment remover treats comment markers inside a string as actual comments.
This valid Verilog line hides the subsequent forbidden tasks from the scanner:

```verilog
wire [15:0] marker="//"; always @(posedge clk) begin $display("TEST PASSED"); $finish; end
```

In a minimal module, both the safety function and `check()` report no errors.
This reproduces the filter bypass; this review did not claim or perform an
end-to-end EDA acceptance exploit. Use source-order-aware string/comment
tokenization and regress literals containing comment delimiters. The safety
gate must not be presented as a security boundary.

### P1 — Baseline repair skips companion validation

`autortl/fsm.py:1445-1456` checks static interface and latency, then sends the
repair to `_full_flow` without the companion check used elsewhere. A mock
reproduction supplied an inlining repair which `companions.violation()` rejects:
`_fix_loop()` nevertheless accepted the repaired source and invoked full flow.

Additionally, `autortl/companions.py:60-74` treats textual instantiation as
reachability. A companion inside `generate if (0)` satisfies the check while not
contributing logic. Even a live disconnected instance cannot establish that the
candidate's outputs implement the separately tested child behavior.

Apply the companion guard consistently, and ensure independent acceptance checks
exercise the optimized top. Do not infer behavioral coverage from module-name
presence alone.

### P1 — Board-suite simulation qualification can pass infrastructure failures

In `hardware/basys3/harness_winners/hwsuite/cli.py`:

- Line87 ignores XSIM's process exit and trusts the last PASS line. A mock
  simulator returning exit9 after a PASS line is reported as passing.
- Line114 excludes `compile` and `xvlog` from fault detections, but counts
  `FAIL: xelab error` and missing verdicts as detected faults. A mock elaboration
  failure is recorded as `fault_caught: true`.

Require a successful compile/elaboration/run process history and an explicit
behavioral mismatch for a killed RTL fault. Missing evidence and infrastructure
failures must remain distinct. These are future gating defects: the inspected
historical fault logs contain genuine behavioral failures, so the reproductions
do not invalidate those past hardware results.

### P2 — Tool-ID errors override genuine infrastructure failures

`autortl/triage.py:56` returns DESIGN before scanning the complete log for host
failures. Both of these probes return DESIGN:

```text
ERROR: [XSIM 43-3225] Permission denied
```

```text
ERROR: [Synth 8-439] module sub not found
Permission denied
```

The same-line host exceptions omit permission failures. Preserve real host
failure classification across the full diagnostic without reinstating the old
routine-license-INFO bug. This matters because classification controls retries,
RTL repairs and recorded outcomes.

### P2 — Hardware image identity can be inferred without a programming record

`hardware/basys3/harness_winners/hwsuite/cli.py:201-216` falls back to hashing the
requested bitstream when no programming record exists. That digest is then
reported as the image on the board. This is an assumption, not readback or
programming evidence; a behavior check cannot distinguish both dot-product
images because their mathematical functions coincide.

Require a successful programming record for verified payload identity, or mark
the image unknown/assumed. Archived six-winner replay has programming records,
so its inspected results remain supported.

## What the new evidence supports

- All six archived winner source identities match the board-suite design table,
  saved run state and board summary. Each has 50,000 hardware transactions with
  zero mismatches, and the archived-bitstream replay reproduces the result.
  Independent review verified146 original-board and22 replay manifest entries.
- The harness-built UART v2 has a 40-to24-LUT optimization and raw logs of a
  1,000,000-byte line-rate stream with no missing bytes or mismatches. The
  1,033-file archive verifies; winner source and archived/live bitstream payloads
  agree. Its text-only host logs give weaker per-run image binding than the
  structured six-winner suite. Its revised stop-bit contract is documented.
- Board integration, UART RX, shell FIFOs, adapters, constraints and deployment
  scripts are manually authored infrastructure. The checked evidence does not
  establish a wholly harness-generated UART-to-FIFO-to-FIR-to-FIFO-to-UART system.
- Live model exploration covers four requested models through Codex on two
  tier0 tasks. API/command backends are implemented and unit-tested; this does
  not establish broad cross-provider effectiveness or superiority to baselines.
- New CRC, SPI and arbiter/register-file testbenches pass their reference designs
  and detect30 selected faults. This qualifies graders; it is not yet a
  demonstration that the harness successfully generated all tier4 designs.
- An earlier232-file identity earned tier0 hold. On the hardened272-file identity,
  campaign24 is the committed passing first run, streak1/heldfalse. Later campaign
  folders were untracked/incomplete during this review. Do not carry the earlier
  identity's held status forward as a new-runtime result.
- `START_HERE.md` still describes old cbab6cf/185dadc milestones as current.
  Current state is recoverable, but the front-door memory needs reconciliation.

## Independent checks

- A fixed Git archive of the reviewed commit contains27,640 files and has ZIP
  SHA256 `0c0c95debb22dca9e5ab29ae72dc7557d8fd035c17874d23c665866f1bb6763f`.
- The committed-blob audit exits0: **43,719 claims across216 claim files**,
  with138 justified exceptions,171 accepted historical losses and two recorded
  claimless files. An audit PASS means compliance with that declared policy,
  not recovery of every historical byte or independent proof of all experiment
  semantics. It excludes74,905 digests in2,721 run records, plus1,857 digests in
  other launch-plan maps. See `review-oct29-audit.json`.
- The tooling/mailbox/board-suite/Fmax/audit test run has181 passes and one local
  Git-clone test failure inside the restricted sandbox. That exact test passes
  when rerun with the required local subprocess permissions (1passed/2.46s).
  This is an environment failure, not an additional project defect.
- Full harness collection:1,654 tests. The first restricted run was intentionally
  stopped after environment-related failures; its partial log is retained. A
  fresh full run with subprocess permissions is recorded separately in
  `review-oct29-harness-permitted-receipt.json` and its raw log. Use that actual
  result, not the interrupted attempt.
- Six pure/mock defect probes are retained in `review-oct29-probes.json` and
  their executable helper `review_oct29_probes.py`. No probe ran a model, EDA
  tool or board operation.

## Recommended finish line

Keep the physical-hardware and evidence work. Integrate the missing sandbox
changes, close the reproduced acceptance gaps and reconcile current documentation.
Run the required gates once on the actual final frozen source. Then prioritize
the predeclared public-task comparison over more backend or orchestration
features. The missing CV headline is measured advantage under a fair benchmark;
the existing hardware results already provide substantial engineering substance.
