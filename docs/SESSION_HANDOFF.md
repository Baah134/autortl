# Session handoff

Updated: 2026-10-20 (America/New_York)

## Start here

Canonical checkout: C:/Users/prince.baah/Downloads/autortl-work.
The separate Downloads/autortl folder predates this work and was preserved.
Read START_HERE.md, AGENTS.md, docs/AGENT_HANDOFF.md and docs/TASKS.md.
Check git status, git log -1 and python scripts/session.py status before editing.

## User decisions

- Use command-line Vivado. MCP remains deferred.
- Different user-authorized AI coordinators may take turns, each using its own
  subagents. Claim the coordinator lease and separate worker file scopes.
- Continue while usage is available. Checkpointing is continuity preparation,
  not a request to stop or switch now. A returning coordinator reads the latest
  shared memory and Git state before continuing.
- The harness runtime currently invokes Codex CLI with the existing login.
  Changing development coordinator does not change the runtime provider.
- Commit and push substantive tested progress to GitHub. The user explicitly
  requested merging the completed checkpoint into main and continuing to improve
  incrementally. Preserve all experiment verdicts and tier promotion gates.
- Preserve progress and evidence for Prince Baah's CV. Do not claim unmeasured
  optimization improvements or autonomous operation from a standalone trial.

## Repository and publication

Remote: https://github.com/Baah134/autortl
Active branch: codex/contract-context. Last published checkpoint 4091a4b;
main includes the public README rewrite f08cb76. Inspect current Git/remote state
because subsequent validated commits may follow this document.
The paused MCP draft remains in its existing local stash.

## Latest harness-focused milestone

The user's priority is harness reliability with weak models, not collecting
impressive design counts. Use designs as experiments. Periodically decide which
features to keep, simplify, improve or remove; docs/HARNESS_REVIEW.md records the
first audit. Weak-model performance is unmeasured.

4091a4b froze authoritative role context, strict evaluator parsing and the
independent counter32 reference testbench. Full suite: 436 passed in 118.53s.
Five real counter reference/mutation cases matched expected verdicts. Together
with earlier generated-testbench cases there are fourteen live verdict checks.

The fresh cohort tier0_fkxbmmwe originally finished 0/2 after Codex exit1.
Both runs were later resumed at the unchanged implementation and finished DONE,
with baselines retained. Counter resumed only the failed evaluator call (7->8
model calls); tool time stayed 267.641s with no repeated physical work.
Its physically valid candidate measured 55->53 LUTs, 37 FFs, WNS .456/WHS .282ns,
but evaluator rejected because context omitted routed timing report identity.
Do not claim accepted improvement. Original failed cohort stays 0/2; no tier held.
Portable raw evidence: evidence/2026-10-20/contract-campaign-01/.
Original worker exit1 causes are unknown; the separate minimal diagnostic passed.

Current repairs add bounded redacted worker diagnostics, typed model-blocked
checkpoints, report manifests including timing, legal mutation/Doctor prompts,
hold-aware diagnosis and actual physical hold-fix command selection. The dead
module artifact-cache branch is removed; journal reuse remains. Unsupported
parallel_candidates=True is explicitly rejected. Final regression suite: 468 passed in134.47s, retained in
evidence/2026-10-20/harness-audit-tests.txt. Source is frozen for a fresh tier0
campaign and supervised physical hold-fix command validation.

## Earlier completed foundation (2026-10-19)

- Relocated the full Git clone and unfinished files; all 317 hashes matched.
- Added provider-neutral instructions for Codex/Claude/Gemini, SQLite coordinator
  leases, exclusive worker scopes, checkpoints, handoffs and a readable export.
- Atomic config/state/budget/cache persistence; strict saved configuration;
  zero budgets; contextual cache verifies matching source and retained reports.
- Journaled build/optimization stages. Interrupted runs replay completed model
  and tool work without spending it again. Unfinished stages may repeat within
  remaining budgets. DONE replay verifies final source, summary and reports.
- Frozen inputs plus implementation/Python/tool identities prevent silent drift.
- Typed JSON build mode, bounded generation/repair, qualified testbenches and
  mandatory top verification. Invalid qualification cannot regenerate its own
  grading. Infrastructure retries preserve RTL and never count as design rejects.
- Exact parameterized/grouped/signed/non-ANSI interface parsing, static width
  checks, valid default-first combinational assignments and token-aware blocks.
- Fixed-latency drain and race-free multiport streaming scoreboard generation.
- Restricted golden functions run in a separate deadline-bounded process with
  a minimal environment. Restricted Python is not a general hostile-code sandbox.
- Real three-run curriculum promotion with cohort and individual evidence gates;
  counter8 and priority-encoder build fixtures with independent top testbenches.
- Removed generated bytecode from source control; ignored runtime state stays local.

## Validation and evidence

Earlier main integration suite: 423 passed in 84.05 seconds, retained in
evidence/2026-10-19/main-integration-tests.txt. The prior 423-test repair run
and earlier 411-test checkpoint remain separately retained.
Portable evidence: evidence/2026-10-19/ (test log, relocation hashes and nine live
Vivado simulator cases with source/testbench hashes and raw logs).
All nine live positive/negative cases matched their expected verdicts.
Earlier Codex-generated counter: 6 LUTs, 8 FFs, WNS 7.806 ns, WHS 0.249 ns at
10 ns on xc7a35tcpg236-1. This is a distinct 8-bit design, not a LUT reduction
against the earlier 32-bit counter (54 LUTs/37 FFs).

The first live tier0 campaign finished 0/2: counter exhausted eight model calls
after rejected contract revisions and a missing-timescale candidate; mux4 was
blocked by missing boundary timing. Both original baselines simulated and routed.
The counter baseline measured 54 LUTs/37 FFs, WNS 5.491 ns with clock-only timing.
New fixes stop unaccepted contracts, save budget stops, prepare timescales and
apply boundary timing in supported Tcl after synthesis. Unsupported XDC control
flow is promoted to ERROR. I/O delay defaults are ideal zero min/max relative
to clk; these are experiment assumptions, not board constraints. Remeasure every
baseline under the new constraints. Counter timescale replay passed without a
model call. Supervised timing replays retain failures as well as successes.
See evidence/2026-10-19/live-tier0/ for exact outcomes and raw reports.
Final supervised mux replay passed with 8 LUTs/8 FFs, WNS 0.579 ns and WHS
0.052 ns at 10 ns. Both boundary missing-delay counts are zero. Replay01 was
rejected and replay02 cancelled before the corrected replay03 passed.
No hardware or test job remains running at this checkpoint.

The full build/resume loop still needs a successful live campaign and real
interruption/resume validation. No tier is claimed newly held. No optimization
percentage or unattended operation claimed.
The main coordinator remains active; subagents have completed bounded provider
and legal-transformation patches for coordinator review.
The checkpoint command retains ownership; handoff releases it on actual exit.

## Exact next work

1. Finish regression validation of provider/provenance/legal-transform fixes at
   one frozen implementation. Do not edit runtime source during tests/live runs.
2. Run fresh bounded tier0 counter/mux experiments with complete report context.
   Preserve original failures; no silent regrading/resume across code changes.
3. Run counter8_build and encoder8_build with independent top TBs, then generated
   golden/TB variants. Measure coverage of each actual harness execution path.
4. Validate live cache reuse/invalidation, process interruption and restart;
   timing Doctor needs live setup/hold repair evidence beyond regression tests.
5. Advance through PWM/accumulator, FIFO/skid buffer, MAC/FIR and UART only after
   independent verification is strong enough. Three consecutive matching full
   qualifying cohorts are required before claiming any tier held.
6. Compare feature ablations and a genuinely available weaker model with frozen
   tasks and budgets. Report calls/tokens/tool time and all failed attempts.

## Local execution

Vivado bin: C:/AMDDesignTools/2025.2/Vivado/bin
Working Python used here:
C:/Users/prince.baah/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
Existing test dependencies:
C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work/review_deps
Use PYTHONDONTWRITEBYTECODE=1, a writable TEMP/TMP, and explicit pytest basetemp.
Approved execution outside the desktop sandbox may be required by Vivado's
Windows launcher. Automatic approval-service usage failures mean the command
was not executed; record the block and retry after access returns.
