# Current session state

Updated: 2026-10-20 (America/New_York). Reconcile this file with Git, coordination
status and actual process state; documentation is not execution evidence.

## Workspace and publication

- Canonical checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
- Separate preexisting `Downloads/autortl` is preserved; do not edit it.
- Remote: https://github.com/Baah134/autortl
- Active branch: `codex/contract-context`, published through `2318e42`.
- Main currently includes `f08cb76`, the public README rewrite after the earlier
  CLI integration. Inspect remote hashes before integrating newer milestones.
- Paused MCP work remains in its original stash; command-line Vivado is active.

## Standing user decisions

The harness is the product. Designs are experiments to improve reliability,
feedback, verification and efficiency, including eventual weaker-model use.
Periodically keep, improve, simplify or remove features based on evidence;
`docs/HARNESS_REVIEW.md` records decisions and missing coverage.

Continue autonomously while access permits. Different user-selected providers
may coordinate, each with bounded subagents. Claim a coordinator lease and
exclusive file scopes through `scripts/session.py`. Checkpoints retain ownership;
handoff releases it only when actually switching or ending. Runtime models
currently use the existing Codex CLI login; changing coordinator does not change
that provider. Do not invent a provider fallback or request new API keys.

Push substantive tested progress. The user requested incremental integration
into main; preserve required regression/benchmark review, actual failures and
three-matching-cohort tier governance. README is for visitors; continuity stays
here, in AGENTS/START_HERE and the progress log. Preserve honest CV evidence.

## Latest completed source checkpoint

Latest published source is `2318e42`: **554 tests passed in148.80seconds**,
plus24actual simulation verdict checks. It adds bounded Windows checkpoint
retries and structural parameter/signed/packed interface preservation.

Its foundation `1243e2e` contains fixed, mechanically rendered optimization contracts. No model
proposes/refines/reviews their wording. Planning, generation and final evaluator
remain; all deterministic promotion gates remain mandatory. Immutable contract,
source, config, runtime and report identities protect replay and DONE reuse.

All roles receive fixed-contract conventions. Active references agree on exact
cycles, resets, widths and parameter semantics. Missing planning guidance is
provided; skill budgets count headers and separators. The referenced FIFO's
combinational full/next-pointer loop is repaired and independently checked.

- Foundation suite at1243e2e: **497 passed in100.04seconds**.
- Initial suite: 496 passed/one Windows CRLF-vs-LF fixture assertion. Corrected
  fixture compares raw decoded bytes; the original failed log is retained.
- Live simulation qualification: nine generated-testbench cases, five counter32
  cases and six FIFO cases matched expected verdicts. Mutants fail actual
  assertions; compile/launch/timeouts do not count as detection.
- FIFO coverage: AW=2/4, DW=8, capacity, blocked writes, data order, empty/disabled
  read hold, wraps, deterministic traffic and coordinated reset. No metastability,
  unilateral-reset or physical multi-clock implementation claim.
- Supervised physical hold command executes in Vivado: mux 18 LUTs/8 FFs,
  WNS 0.579 ns/WHS 0.059 ns; standard flow used 8 LUTs/8 FFs. Keep it targeted.
- Typed provider failures retain bounded redacted diagnostics and save
  `model_blocked`, best pointer and spent budgets without rejecting RTL.
- Removed unreachable module artifact-cache branch; verified journal reuse
  remains. Unsupported `parallel_candidates=True` now fails explicitly.

Portable evidence is under `evidence/2026-10-20/`, with hashes and raw reports.

## Current experiment and prior failures

Campaign03 finished 1/2 under `logs/contract-campaign-03/tier0_c05h57lo`
at the frozen 1243e2e runtime. Mux completed with three model calls and retained
its baseline; counter stopped after passing simulation when a budget checkpoint
replacement raised WinError5. Original results are archived in contract-campaign-03.

Checkpoint `2318e42` publishes bounded Windows checkpoint retries and structural
parameter/signed/packed interface preservation. **554 tests passed in148.80s**;
all four new signed/parameter live checks match expected verdicts.

Campaign04 completed at frozen2318e42 under
`logs/contract-campaign-04/tier0_2_c6uspo`: **2/2 mandatory gates**, first
qualifying cohort under its historical governance, not held. Three model calls
each; neither candidate promoted. It cannot count toward a new runtime-bound
streak after the current governance repair.
Counter53vs55LUT passed physical verification but review rejected missing actual
process exits in context. Mux8LUT had no gain; its review exposed inferred
zero-latency metadata despite an unannotated registered original. Raw outcomes
are archived in evidence/2026-10-20/contract-campaign-04 (185 hashed files).

Current uncommitted work closes those gaps: durable actual process receipts,
deterministic receipt gating, cache/DONE retention, source-bound Doctor
verification reuse, explicit unknown source latency, UTF8 skill loading, and
frozen-runtime curriculum identity. All runtime edits and fixtures are frozen. **655 tests passed in207.64seconds**
after the seven legacy fixture updates; initial648pass/7fail log is preserved.
All54runtime/governance identities match the frozen test manifest. Publishing
this tested development checkpoint, then launch fresh campaign05 with the same
bounded counter/mux tasks. No runtime edits during that campaign.

Earlier original cohorts remain failures:

- Campaign01 originally 0/2 after unknown worker exits. Separate unchanged-code
  recovery reached DONE with baselines retained. Counter retried one evaluator
  call (7 to 8), no repeated physical stages, tool time unchanged at 267.641 s.
  Its measured 55-to-53 LUT candidate was rejected due omitted timing report
  identity. Never report it as an accepted autonomous gain.
- Campaign02 at 61854c0 finished 0/2: counter spent six negotiation calls then
  blocked on wording; mux saved a real CODEX_QUOTA model block after its baseline.
  These motivated the fixed contract. Preserve original denominators.

One later minimal readiness call returned READY. It is separate from campaign
budgets; CLI model identity was not returned. No weaker-model performance or
held tier is established by these results.

## Exact next actions

1. Collect receipt/latency/governance worker results; independently review, run
   the full regression suite, publish a tested checkpoint, then fresh campaign05.
   Never resume campaign03/04 across implementation changes.
2. Fix reproduced harness defects with tests and taxonomy, using a fresh run
   directory after changes. Never weaken independent tests or acceptance gates.
3. Exercise typed counter8/encoder8 builds with independent top tests, then the
   generated golden/TB path. A compile or mocked build is not a live build result.
4. Validate live cache reuse/invalidation, full process interruption, restart,
   best-of-N diversity and complete Doctor invocation. Existing regression tests
   and supervised tool trials do not establish all these execution paths.
5. Run controlled feature ablations and an actually available weaker model with
   frozen tasks/budgets before making robustness claims. Progress toward PWM,
   FIFO/skid buffer, MAC/FIR and UART as independent verification strengthens.
6. Update progress/task/audit records, publish meaningful milestones and verify
   remote hashes. Three matching full qualifying cohorts are required to hold
   a tier; one passing cohort is insufficient.

## Local tools

- Python: `C:/Users/prince.baah/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`
- Test dependencies: `C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work/review_deps`
- Vivado binaries: `C:/AMDDesignTools/2025.2/Vivado/bin`.
- Use explicit workdir, PYTHONDONTWRITEBYTECODE=1, test PYTHONPATH and unique
  pytest basetemp under the writable workspace. Keep one Vivado job queue.
- Downloads writes, Git metadata/network and vendor launchers may need the
  approved execution profile. Record a rejected action as not executed.
