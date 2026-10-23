# Development evidence log

Project owner: Prince Baah. AI-assisted review and development are recorded
separately from the owner's project direction and prior implementation.

## 2026-10-15 — Review baseline

- User defined the autonomous design/improvement objective and requested
  a full review and progressive development with a CV evidence log.
- Reviewed base commit `ee255942452f4d021d289512830f63d1cdb3c035`.
- Existing suite: 91 tests passed in 4.30 seconds, Python 3.12. These were
  existing tests, not tests newly authored during this work.
- Controlled probes found serious verification, build, resume, and export
  defects. Full review and reproduction JSON remain in workspace outputs.
- No verified hardware improvement. Historical README LUT savings remain
  unreplicated by this work.

## 2026-10-15 — CLI access and durable handoff

- User selected command-line Vivado and requested continuity across sessions.
- MCP protocol discovery had worked (41 tools), but its live launcher failed
  under the sandbox. MCP draft preserved in local stash; setup deferred.
- GitHub connector reports read/write permission. No remote changes made.
- Retried the previously blocked bounded CLI smoke using approved execution
  outside the sandbox. Vivado 2025.2 batch mode completed with exit code 0.
  Tcl printed version 2025.2, arithmetic result 42, and the success marker.
- Invocation: `vivado.bat -mode batch -source check.tcl -nojournal -nolog`.
- Added AGENTS.md, SESSION_HANDOFF.md, and this log on `codex/cli-bringup`.
- Scope of evidence: tool startup and Tcl execution only. No simulation,
  synthesis, timing, area, power, or optimization success claimed.
- Next: bounded counter simulation/synthesis, followed by integrity repairs.

## 2026-10-15 — Verification repairs and live counter checks

- User authorized iterative improvements and testing; command-line flow retained.
- Simulation verdicts now reject mixed pass/failure logs and bare termination.
- Mutation qualification requires a passing control and explicit testbench
  rejection of the mutant. Missing mutations, compile failures, timeouts, and
  infrastructure failures cannot qualify it. Regenerated testbenches requalify.
- Candidate synthesis and metrics cache access require simulation rung 4.
  Unknown/infrastructure results do not trigger candidate RTL repairs.
- Tests: 128 passed in 4.47 seconds (37 new regression cases; original 91
  retained). An initial test-authoring error omitted RunConfig.mode; corrected
  before the passing runs. `git diff --check` passed.
- Real xvlog/xelab/xsim reproduced two counter assertion failures due to an
  extra enabled clock edge. Fixed stimulus, reset race, and unknown-value
  checks; added watchdog and DUT timescale. Corrected counter simulation passed.
- Live mutation qualification passed: changing the first `<` comparison to
  `>` produced two assertion failures while the original passed.
- Initial synthesis failed with Common 17-53: get_ports executed before an
  open design. XDC generation now preserves the query literally. Added a
  driver regression and infrastructure classification for that specific error.
- Counter synthesis, placement, and routing completed after the XDC fix:
  xc7a35tcpg236-1, 10 ns clock, 54 LUTs, 37 FFs, WNS 5.491 ns, WHS 0.276 ns.
  Raw reports confirm these baseline measurements; no optimization gain claimed.
- Comparing raw reports exposed a hold-slack parser defect: combined timing
  tables reused the setup-slack column. Fixed column mapping and require both
  setup and hold slack for timing_met. Added real-report fixture regressions.
- Added `scripts/check_counter_cli.py` for repeatable model-free evidence
  collection. CLI help and four control-flow/evidence regression cases passed;
  complete live script execution passed simulation, mutation qualification,
  synthesis and routing with exit code 0. Repeated metrics matched 54 LUTs,
  37 FFs, WNS 5.491 ns and WHS 0.276 ns.
- The live script started before a metadata cleanup: its raw result retains
  `metrics.sim_error = Simulation log not found` because implementation and
  simulation use separate directories. Its explicit simulation section and
  simulation log pass. The script now clears that stale diagnostic when
  attaching verified simulation evidence; covered by a unit regression.
- Evidence remains in workspace `work/counter_cli_evidence*`,
  `work/counter_implementation_*`, `work/counter_cli_complete`, and
  `outputs/AutoRTL-tests-2026-10-15.txt`. The repeat-run JSON records source hashes.
- Full tier benchmarks not run; no merge, no held-tier claim, no autonomous
  improvement or area-saving claim. Baseline/resume/restart defects remain.

## 2026-10-16 — Codex-only workers and recovery from interruption

- User no longer has access to previous providers and authorized Codex-only
  workers with main-agent supervision and iterative implementation/testing.
- Development helpers implemented provider integration and baseline/restart
  repairs; independent reviewer checked them. Main agent integrated changes,
  strengthened metrics checks and authored the supervised generation trial.
- All active roles route to codex.default. Missing-YAML fallback is Codex-only;
  legacy adapters cannot be selected through the active registry. Existing
  login and configured default model are retained; auth/config were not changed.
- Worker calls use stdin, ephemeral temporary CWD and read-only sandbox.
  Completed JSONL and nonempty final response required. Unknown model/cost
  stays null. Attempts charge budget before launch; timeouts are bounded.
- Baselines without verification or valid metrics cannot be promoted. Exact
  infrastructure/unknown tool verdicts prevent RTL repair. Restart changes
  generation seed without overwriting winning source/metrics.
- Setup/hold sentinel and nonfinite metrics now fail the shared gate.
- Full suite: 202 tests passed in 6.94 seconds. Initial integration run exposed
  sandbox temp-directory access and zero-call budget edges; corrected.
- Live trial01: a Codex generator returned an 8-bit counter in 5.75 seconds;
  reported usage 15,447 input tokens (12,032 cached), 92 output tokens.
  Actual model identifier and monetary cost were not reported.
- Trial01 static checks, 700-cycle reference simulation and stuck-zero mutant
  detection passed. Implementation timed out after 300 seconds. An orphaned
  Vivado process was confirmed by exact script path and terminated by parent.
  No routed result or improvement claimed for trial01.
- Added Vivado Popen process-tree cleanup, bounded draining and retained partial
  logs. Codex timeout/cancel cleanup also avoids blocking Windows pipe closure.
- Independent review strengthened the counter testbench to test reset away
  from clock edges, added an asynchronous-reset mutant, required timing closure
  and charged elapsed tool runtime. Replay uses saved RTL, with no model call.
- Automatic approval review previously prevented trial02 from starting because
  of a usage limit (not a safety rejection). User continued; bounded retry on
  2026-10-16 was approved and completed successfully.
- Trial02 reverified the exact trial01 RTL hash
  `52533d4a6c66c3e74c0bf1475641d55a25334dba12b304592c34466296900a2f`.
  All stages passed: static, 700-cycle simulation, stuck-zero detection,
  asynchronous-reset detection, synthesis/place/route, metrics, timing.
  Device xc7a35tcpg236-1, 10 ns clock: 6 LUTs, 8 FFs, setup slack 7.806 ns,
  hold slack 0.249 ns. This is an 8-bit generated design, not an improvement
  comparison against the earlier 32-bit counter.
- Trial02 made no model call. Its raw kind field predates the replay-label
  correction; source_import and imported_source identify it as reverification.
  New runs label replay supervised_reverification. Raw evidence is preserved.
- Additional review repairs: total simulation deadline shared across compile,
  elaboration and simulation; trial timeouts capped by remaining tool/wall budget.
- Timing Doctor now uses isolated trials and adopts source, metrics and report
  directory together after verification and metric gates. Invalid cached metrics
  cause fresh synthesis. Full cache context keys remain future work.
- Evidence: work/codex_counter_trial_01, work/codex_counter_trial_02,
  outputs/AutoRTL-codex-tests.txt. Final integrated suite: 226 passed in 9.10s.
  Independent review found no checkpoint-blocking doctor regression. Valid
  cache report provenance remains incomplete. Work checkpointed locally on
  codex/cli-bringup; no remote publication or merge. Full tier gates not run.

## CV evidence policy

Record failures as well as successes. Quantitative claims require matching
source hashes, testbench, device, constraints, tool version, and baseline
and candidate reports. Document seeds, budgets, and number of trials for
autonomy claims. A passing startup check is not an autonomous design result.

For each future entry record: objective, user decision, branch/commit,
changes, commands, outcomes, evidence locations, limitations, and next action.

## 2026-10-19 — shared memory, Downloads workspace and recoverable stages

- User decision: continue while usage is available; another provider can take
  over when needed, and returning agents resume from the latest repository.
  Checkpointing must not itself release the active coordinator or stop work.
- Canonical clone moved to C:/Users/prince.baah/Downloads/autortl-work;
  317 file hashes matched. The separate existing Downloads/autortl was preserved.
- Published earlier tested milestones through 68fc5e6 to origin/codex/cli-bringup.
  This checkpoint is committed and pushed to the same development branch.
  Resolve its exact revision with git log; main remains unchanged pending gates.
- Added provider-neutral START_HERE, decisions/task board, SQLite coordinator
  leases and worker scope claims, active checkpoints and explicit exit handoffs.
- Integrated atomic config/state/budget/cache persistence and source/report
  provenance, replayable model/tool stage journal, bounded infrastructure retries,
  input/runtime drift checks, validated DONE replay and typed JSON build flow.
- Repaired fixed-latency and streaming testbench generation, isolated restricted
  golden execution, exact Verilog interface checks and blueprint identifier/wiring
  validation. Added three-cohort curriculum governance and counter/encoder fixtures.
- Validation: bundled Python -m pytest tests/ -q -p no:cacheprovider with explicit
  writable basetemp, PYTHONDONTWRITEBYTECODE=1 and local review_deps PYTHONPATH.
  Final outcome: 411 passed in 66.27 seconds. Includes interruption, replay,
  tampering, infrastructure, config, ownership/concurrency and build regressions.
- Nine real Vivado simulator cases all matched expected positive/negative verdicts.
  Portable source/testbench hashes and raw tool logs: evidence/2026-10-19/.
- These are controlled full-FSM tests plus live testbench cases, not yet proof of
  a live autonomous optimization campaign. No new held tier or improvement claimed.
  Next: bounded tier0 counter/mux campaign, then counter8/encoder builds and real
  interruption/resume checks. Keep recording unsuccessful attempts as evidence.

## 2026-10-19 — first live cohort, reproduced failures and verified repairs

- Continued after publishing 8d5eb09 and d1a02fb; no provider handoff requested
  or performed. Remote and local development hashes matched; all 69 first
  checkpoint evidence files were restaged to preserve exact original bytes.
- Executed run.py bench --tier 0 --iterations 1 --best-of-n 1 with explicit
  Vivado 2025.2 paths, eight model calls, twelve Vivado minutes, eighteen wall
  minutes and one infrastructure retry per design. Original cohort result 0/2;
  no tier held and no optimization claimed. Raw inputs, stage responses, budgets,
  events, reports, source hashes and manifests are archived in live-tier0/.
- Counter baseline reproduced: 54 LUTs, 37 FFs, WNS 5.491 ns under the old
  clock-only constraints. Rejected contract revisions consumed the model budget;
  its candidate hit XSIM 43-4099 for an omitted timescale. No candidate promoted.
- Mux baseline simulated/routed but its boundary paths were unconstrained;
  missing timing was correctly rejected. Kept the fail-closed metric policy.
- Fixed three-review negotiation to require actual ACCEPT; no unreviewed final
  refinement executes. Explicit model/tool budget exhaustion saves a non-success
  summary. Generated/fixed/doctor RTL gets a default timescale while explicit
  timescales and raw latency headers are preserved. Added vendor error fixtures.
- Added ideal synchronous zero min/max I/O delay assumptions relative to clk.
  The first replay exposed unsupported `if` in XDC (Designutils 20-1307).
  Stopped only the verified owned second launcher when the same invalid script
  was recognized. Preserved both attempts. Corrected to source conditional Tcl
  after synthesis, promoted the unsupported-XDC diagnostic to ERROR, and added
  a command-order regression test. Never reduced a tool severity.
- Supervised replay03, with zero model calls: counter candidate simulation
  passed after timescale preparation. Mux simulation, synthesis, routing and
  timing passed: 8 LUTs, 8 FFs, WNS 0.579 ns, WHS 0.052 ns at 10 ns on
  xc7a35tcpg236-1. Both missing input/output delay counts are zero. Synthesized
  hold violations were repaired during routing. This is validation, not an
  autonomous optimization or a comparison with the 32-bit counter.
- Full pytest at unchanged implementation: 423 passed in 62.33 seconds.
  An earlier overlapping test attempt was invalidated when implementation
  changed; its resume drift check correctly refused replay. That log is retained.
- Evidence: evidence/2026-10-19/live-regression-tests.txt and live-tier0/.
  Four archives have SHA256 manifests; raw bytes are preserved in Git. No Vivado
  or test process remains running. Checkpoint keeps coordinator ownership.
- Next: supply authoritative harness facts to contract roles; run fresh bounded
  tier0 experiments with new I/O-constrained baselines, then independent build
  fixtures and real interruption/resume. A successful autonomous cohort is still
  pending. Required main-merge tier gates have not passed.

## 2026-10-19 — user-requested integration into main

- User requested the next plan and explicitly instructed merging all completed
  work so the project can improve incrementally. This authorizes integrating
  the current tested checkpoint before the previously documented held-tier gate.
  Hardware acceptance and tier promotion results remain unchanged.
- Fetched origin and confirmed main had no independent remote commits. Used
  fast-forward-only merges, preserving all six development commits through
  387fe0e. No history rewriting or source conflict resolution was needed.
- Pushed main from ee25594 to 387fe0e and verified its exact remote hash.
  Existing development branch remains available. The paused MCP stash was not
  part of this completed CLI checkpoint and remains preserved.
- Reran the full unchanged implementation on main: 423 passed in 84.05 seconds.
  Evidence: evidence/2026-10-19/main-integration-tests.txt. This merge performs
  no new Vivado benchmark; prior supervised replay evidence remains applicable.
  The first autonomous cohort remains 0/2; no tier or optimization gain claimed.
- Updated README, START_HERE, session handoff, decisions and task board to use
  current main and preserve the exact known validation gaps.
- Next sequence: provide authoritative harness context to contract proposal and
  review; run a fresh bounded counter/mux cohort under the same explicit I/O
  assumptions; fault-inject and resume a real run; validate counter8 and priority
  encoder builds before progressing to PWM, buffering and larger datapaths.


## 2026-10-20 - Harness evidence, real recovery and feature audit

- User reiterated that the harness is the product; designs are experiments.
  Published README rewrite f08cb76 keeps public purpose/results separate from
  provider continuity. Checkpoint4091a4b (436 tests in118.53s) is on development.
- Independent counter32 reference checks all outputs, reset/load/enable priority,
  threshold highbits, registered flags and overflow over880+checked edges.
  Five actual Vivado cases matched verdicts: original passes, four mutants
  trigger assertions. Archive counter32-reference includes raw logs/hashes.
- Fresh cohort tier0_fkxbmmwe originally0/2 after unknown worker exit1; baseline
  counter55LUT/37FF WNS.494/WHS.113; physically valid candidate53LUT/37FF
  WNS.456/WHS.282. No candidate accepted. Both same10ns/idealzeroI/O constraints.
- At unchanged4091 implementation, counter recovery repeated only evaluator
  (7->8model calls), no completed tool stage and unchanged267.641s physical time.
  Evaluator rejected due omitted timing-report identity, which exists in archive.
  Mux recovered DONE with8LUT baseline retained. Original cohort stays0/2.
- Feature audit docs/HARNESS_REVIEW.md keeps deterministic verification,
  independent mutation checks, metric integrity, journals and immutable facts;
  prioritizes provider/evidence boundaries, legal transformations and eventually
  machine-defined optimize contracts. N=1 does not establish best-of-N benefit.
  Golden/build/cache/restart/Doctor paths still need separate live experiments.
- Provider worker now retains bounded redacted error diagnostics; quota/auth
  stops immediately, network/timeout retries remain bounded. Typed failure
  checkpoints record model_blocked without changing RTL/design rejection history.
- Timing/utilization manifests include complete file identities and bounded
  previews; legal mutation/Doctor advice preserves cycle/reset/parameter behavior.
  Canonical setup/hold diagnosis selects physical hold fixing, not extra RTL cycles.
  Removed dead module-cache read/write path; journal reuse remains. Unsupported
  parallel execution is rejected explicitly. Weak-model performance unmeasured.
- Initial integrated focused tests83passed51.62s; final full-suite validation
  follows review fixes. No live optimization gain or new tier is claimed here.

- Final full suite at frozen repaired implementation: **468 passed in134.47s**;
  evidence/2026-10-20/harness-audit-tests.txt. Includes model-blocked early/late
  replay with preserved budgets, budget-stop best pointer, power provenance,
  hold-fix command selection and all prior regressions. The first staged check flagged a trailing blank fixture line;
  this is normalized in the subsequent evidence checkpoint. New live campaign follows at this tested revision.

- Supervised physical hold-fix command check passed at61854c0: mux simulation
  passes; `phys_opt_design -hold_fix` accepted by Vivado2025.2; preplaceWHS-1.057ns
  becomes routedWHS.059ns withWNS.579ns. Cost18LUT/8FF vsstandard8LUT/8FF.
  Archive physical-hold-fix preserves raw source/scripts/reports/hashes. This
  validates the command path, not a complete autonomous Doctor invocation or
  isolated causal optimization benefit. Fresh bounded tier0 campaign follows.


## 2026-10-20 - Remove model negotiation and reconcile actual skill prompts

- Continued at user request after quota interval; reclaimed expired coordinator
  lease and reconciled saved changes before edits. No prior process assumedlive.
- Frozen campaign02 at61854c0 finished0/2. Counter baseline55LUT/37FF passes;
  six contract calls/three reviews blocked wording without generating RTL.
  Mux baseline8LUT/8FF passes; first planner call saved typed CODEX_QUOTA with
  bounded diagnostics, spentcall1 and best_iteration0. No repair/designrejection.
  Portable archive contract-campaign-02 preserves both failures and raw evidence.
- Replaced negotiable optimization prose with a contract rendered mechanically
  from immutable evidence. Source/TB/device/constraints/objective remain fixed;
  final evaluator and deterministic verification/promotion gates remain required.
  Contract modification/deletion fails both interrupted and DONE replay.
- Audited actual injected references: removed instructions to add latency,
  change resets/parameter semantics or invent timing exceptions. Added missing
  fpga-methodology; all role calls now receive conventions exactlyonce. Skill
  injection budgets include reference headings and separators.
- Repaired referenced FIFO combinational full/next-pointer loop using current
  registered writegraypointer. Independent dualclock TB and two-depth control/
  data/full mutants prepared; no physical CDC or metastability proof claimed.
- Focused actualrole/skill tests22passed0.52s; final combined validation follows.

- FIFO live qualification:6/6expectedverdicts inactualVivado xsim atAW2/AW4,DW8;
  controls pass, read-data and full-comparator mutants trigger assertions.
  Archive fifo-reference retains independentTB/sourcehashes/logs. No physical
  CDC or metastability claim. Minimal provider readiness call returnedREADY;
  its usage is separate from experiment budgets, modelidentity unavailable.

- Final combined suite: **497 passed in 100.04 seconds**, retained in
  evidence/2026-10-20/fixed-contract-tests.txt. Initial combined run retained
  496 passes and one Windows CRLF/LF fixture assertion; the corrected test
  compares raw decoded bytes consistently with the production evidence path.
- Verified all 160 newly archived physical-hold/FIFO/campaign02 file hashes.
  New source is frozen for a fresh bounded counter/mux campaign. Model access
  readiness passed with one separate minimal call; model identity was not
  returned by the CLI, so no specific model-strength claim is made.


## 2026-10-20 - Windows persistence and structural interface enforcement

- Campaign03 at1243e2e finished **1/2**. Mux completed all stages with three
  model calls; its 8-LUT candidate had no gain, so the baseline was retained.
  Counter reached candidate generation in two calls and passed simulation, then
  hit WinError5 replacing budget.json. Its last persisted budget may omit that
  interrupted charge; no exact accounting recovery or physical gain is claimed.
- Added bounded Windows atomic replacement retry for errors5/32/33: seven
  attempts, at most0.63seconds backoff, same flushed sibling file, previous
  target preserved, original error retained, cleanup cannot hide write errors.
  Focused19tests include an actual Windows sharing-lock/release case.
- Reproduced and closed six structural bypasses: public default changes/removal,
  public-to-local conversion, signedness drift, parameterized-width hardcoding
  and packed range reversal despite equal default widths. Public parameters
  are separated from internal constants; interface-relevant symbolic dependency
  declarations are retained conservatively. Compatible non-ANSI declarations
  remain supported; ambiguous merges fail explicitly.
- Shared typed declarations preserve signedness and packed shape in stubs,
  generated top/wires/TBs and role prompts. Fallback qualification uses the
  same interface stub. Golden models retain masked bit patterns with explicit
  signed interpretation; no automatic change of software oracle semantics.
- Full frozen suite: **554 passed in148.80seconds**. Four new real Vivado cases
  pass expected verdicts: signed control/unsigned mutant and symbolic-parameter
  control/stuck-zero mutant under W12/EXTRA1. Runtime hashes match source used
  for tests. Total retained simulation verdict checks24; physical hold check
  remains a separate supervised experiment. No general parameter proof claimed.
- Portable evidence: interface-atomic-tests.txt, signed-interface/ and
  contract-campaign-03/. Fresh full tier0 campaign follows at the new revision.


## 2026-10-20 - Fresh complete cohort and evidence feedback

- Frozen2318e42 campaign04 finished **2/2 mandatory gates**, first qualifying
  cohort, not a held tier. Counter and mux each used three model calls. No
  Windows checkpoint error recurred; no candidate was promoted.
- Counter candidate53LUT/37FF, WNS0.456ns/WHS0.282ns passed the physical
  ladder but was rejected because evaluator context lacked actual process exits.
  Baseline55 retained. Mux8LUT matched its baseline and was rejected.
- Mux review also exposed unknown source latency being presented as zero.
  Repairs are in progress for explicit unknown metadata and process receipts;
  original decisions are preserved, never retroactively regraded.
- Archived185 files under evidence/2026-10-20/contract-campaign-04 with raw
  source/reports/contracts/budgets/journals/runtime hashes and console output.

- Implemented actual subprocess receipts, strict latest-exit/raw-log checks,
  baseline/candidate deterministic evidence gates, cache/DONE integrity and
  source/TB/ordered-companion verification input manifests captured inside the
  successful journaled stage. Replay cannot restamp changed files as verified.
- Physical-only Doctor evidence cites prior source-identical simulation and
  checks its original inputs; missing or changed proof blocks as infrastructure,
  not a scored RTL rejection. Typed builds/TB generation require known latency.
- Fixed locale-dependent guidance loading with explicit UTF8 and a Unicode
  fixture. Curriculum identity binds runtime/Python/tools and governance code;
  missing or mixed identity cannot qualify. CLI model identity stays unobserved.
- Initial combined suite:648passed/7failed in205.97seconds. All seven old
  fixtures claimed successful tool results without supplying the newly required
  receipt evidence; retain the log and adapt fixtures without weakening gates.

- User requested ongoing research into comparable harnesses, with additions
  only after careful reasoning about an actual need. Reviewed ten primary
  source groups; docs/RESEARCH.md records mechanisms, fit, adoption triggers
  and experiment criteria. AGENTS/START_HERE preserve this policy for later
  coordinators. No external code, framework or dependency imported.

- Final combined suite: **655 passed in207.64seconds**. The seven controlled
  fixtures now emit explicit synthetic receipts; negative assertions and
  production evidence gates remain intact. All54frozen runtime/governance
  hashes match the tested source. Publishing the checkpoint before fresh05.

- Published71910e5, then5d285c0 to include the already-tested conventions file
  omitted from the first staging set. No runtime bytes changed during the live
  run: all54test identities and the active runtime manifest were compared and
  matched. Campaign05 started over71910e5 with that unstaged file;5d285c0
  publishes the complete tested runtime. Preserve this provenance distinction.

- Fresh05 counter completed with an **accepted55to53LUT reduction (3.64%)**,
  FF37unchanged, WNS0.456ns/WHS0.282ns. Static/interface, independent frozenTB,
  actualtool exits, routed reports, machineevidencegate and8/8finalreview
  criteria passed. Three model calls;486.673toolseconds. This is one bounded
  Artix7/Vivado2025.2/10ns/ideal-zero-I/O experiment, not general weak-model proof.
- Actual CLI DONE replay returned the same accepted winner with exact unchanged
  budget, summary and winner hashes; no further model/tool calls. This validates
  completed-run replay only, not hard-kill/in-flight process recovery.
- Full05 mux outcome is still pending. Preserve that distinction before a
  cohort claim or main integration.

- Related-work review also checked CRADLE's actual setup: LatticeECP5 with
  Yosys/nextpnr and ModelSim. Removed DESIGN's direct numerical target against
  those unmatched benchmark averages; retained the relevant bounded optimizer/
  rewriter pattern and explicit comparability requirements in RESEARCH.

- Full fresh05 finished **2/2**, runtime-boundstreak1/heldfalse. Mux candidate
  used8LUT with WNS0.579ns/WHS0.057ns and was correctly rejected for no area
  gain; retainedbaseline8LUT/8FF WNS0.579ns/WHS0.052ns. Three calls and
 381.297chargedtoolseconds for mux; six role calls across the whole cohort.
- Archived and hash-verified203files in contract-campaign-05, including actual
  source/TB/metadata, receipts, verified-input manifests, routed reports,
  evaluator decisions, budgets, runtime identity and actual DONE replay records.
  Runtime identity is known; CLI model identity remains explicitly unobserved.
- Integration gate now has655passingtests plus a fresh qualifying fulltier0
  campaign; no higher tier is held. Main will fast-forward to the reviewed
  source/evidence checkpoint, preserving all earlier failed cohorts.

- Main integration completed: both remote main and codex/contract-context
  verified at251666d538cc0e7d51bd5b6994626ec280274471. Local main was advanced
  without checking out or rewriting the frozen runtime. Tests655/655 and full
  tier0 2/2 satisfy the current integration gate; no higher tier is held.
  All campaign jobs finished, archive manifests verified, and working source
  matches the tested runtime. Next work is independent typed-build verification.


## 2026-10-20: generated build and streaming progression (active)

- User requested continued harness improvements followed by more complex designs.
  Followed RESEARCH's independent-verification priority rather than adding agent
  frameworks. Three bounded workers handled distinct fixture/qualification scopes;
  the coordinator owns the serial Vivado queue and integration review.
- Independent counter/encoder testbenches: ten actual simulator cases matched
  expected verdicts (two controls, eight compiling faults). Counter checks now
  include pre-edge hold and reset priority from a nonzero state. Raw logs and
  receipts are in logs/build-tb-qualification-01 pending portable archive.
- First generated counter build (build-golden-counter8-01) failed after one model
  call: generated reference required rst but expected_outputs omitted it. Preserved
  failure; added reset-prefix/deasserted control protocol, explicit temporal model
  prompts, bounded example anchors and one diagnostic oracle repair attempt.
  Provider/storage failures stay separate from generated-program errors.
- Actual scoreboard regression reproduced: a reset-gated combinational pass-through
  passed a latency=1 contract. After accepted-transfer age checking, the registered
  control still passes and the same forbidden design raises eight real assertions.
  Before/after raw evidence remains under logs/scoreboard-latency-{before,after}.
- Added independently authored two-entry eight-bit ready/valid buffer fixture,
  queue TB and eight faults. Ready is explicitly combinational; no registered-ready
  isolation claim. Unit tests establish fixture construction only; live qualification
  and generated build are pending.
- Focused runtime/qualification tests: 60 passed in40.69s; latency/reset/TB tests:
  35 passed in2.37s. Initial full suite: 725 passed, three legacy unmocked-oracle
  fixtures failed in261.52s. Added explicit model mock, preserving negative assertions;
  final full-suite rerun pending. Initial raw failure output retained.
- Counter build02 has already exercised a real syntax-error oracle rejection and
  successful single diagnostic retry, then passed child simulation and injected
  increment fault. Final routing/independent integration verdict still pending.


- Corrected full suite: **743 passed in203.40seconds**. Counter build02 completed
  with baseline retained6LUT/8FF,setup0.424ns,hold0.226ns; same-area candidate
  rejected. Six calls and300.515chargedtoolseconds. Exact saved winner+child
  passed the independently qualified700-cyclecounterTB. Archives: golden-verification
  and generated-counter (including firstbadPython and actual diagnostic retry).
- Publishing this tested development checkpoint. Main remains at the previous
  fully gated campaign until freshfulltier0 and remaining final fixes are validated.
  Skid qualification is running serially; no final streaming result yet claimed.


- Streaming independent TB admission completed: **9/9 expected verdicts**. Correct
  ring-buffer control passes; eight faults assert. Control checks893cycles,
  679accepted/675retired/4resetdiscarded,580simultaneoustransfers and3occupiedresets.
- Read-only worker review caught a general long-latency serial drain bound and
  maximum-batch reset overhead issue. Added taxonomy first, budget per transaction,
  validate data+reset before allocation; focused38tests pass in2.36seconds.
- Real serial100-cycle device: same DUT fails reproduced old168-cycle limit, passes
  corrected368-cycle allowance. This is a repaired harness false rejection, not a
  mutant kill. Source frozen for fullsuite03 and fresh encoder build01. Portable
  evidence streaming-qualification includes raw sources/TBs/logs/receipts/helpers.


- Final serial/reset-budget full suite: **746 passed in272.44seconds**. Publishing
  tested source and streaming qualification; source frozen during encoder live run.
- Next necessary acceptance check: a payload-only streaming scoreboard may accept
  a capacity-one implementation of the capacity-two contract. Independent TB must
  gate child repair and every integrated optimization candidate, while generated
  golden models still run. Plan an explicit opt-in combined mode after reproducing
  that gap; retain default trusted-only behavior and configuration/resume identity.


- Encoder build01 completed on978c742: accepted **6to5LUT (16.67%)**,4FF,
  setup0.531ns/hold0.156ns;5calls,495.720chargedtoolseconds. Exact promoted winner
  independently passes all256patterns in both directions plus registered/reset
  checks. Archive generated-encoder preserves actual physical/evaluation records.
- Capacity-one experiment confirmed payload-only false acceptance; identical DUT
  bytes fail independent capacity assertions. Added explicit combined mode after
  measuring the need. Child fixes rerun both TBs; both qualify; original independent
  topTB gates baseline/candidates. No new agent framework/provider was added.
- Config/CLI90tests pass; flow22tests pass after two fixture corrections (bounded
  infra retry count and explicit candidate-repair mock). Initial log retained.
- Desktop/tool delay interrupted execution around20:15to23:35UTC. Reconciled Git,
  renewed lease; no vendor job was active during the gap. Fullsuite04 and actual
  combined streaming build logs/build-golden-skid-01 are now running on frozen
  source. Budgeted run uses20calls/25toolminutes/40wallminutes/oneinfraretry.


- Combined-mode full suite **774 passed in178.95seconds**. First live streaming
  source passed generated and independent TBs, then correctly STOPPED: the selected
  readiness mutation passed the payload-only grader, so qualification was not
  established. No integration/routing result. Retain generated-streaming-attempt-01;
  do not resume across runtime fixes or silently replace its result.
- Next fix: bounded alternative observable sabotage, keeping missed faults and
  the exact TB unchanged. Also preserve exhausted infrastructure causes as typed
  build-blocked outcomes. Independent temporal tests remain mandatory; portfolio
  qualification is only minimum non-vacuity evidence, not completeness proof.


- Qualification portfolio and typed blockers:54combinedfocusedtests pass; source
  frozen for full05 and streaming02. Full05: **794passed4377.09s** including an
  observed system-sleep interval; no test failures. Runtime duration is not a
  performance claim. First-primary miss remains in JSON; zero-output probe asserts,
  independentTB detects the original readiness mutation in the real streaming run.
- Windows System events42/1 confirm battery sleep2026-10-20T23:48:54.466Z through
  2026-10-21T00:57:19.970Z. Streaming02 exhausted frozen budgets (TOOL_BUDGET,
  no best/physicalresult);2modelcalls,4441.221chargedtoolseconds including sleep.
  No budget reset, design-rejection history or changed-source resume was used.
- AC power confirmed after wake. A temporary SetThreadExecutionState system-awake
  request is active in a local helper for the verification queue, limited to two
  hours and released when work/autortl-verification-active.flag is removed. It does
  not change the power plan. Helper process session53742. Currentvendorqueue:
  logs/build-golden-skid-03; fullsuite06 rerun concurrently. Source remains frozen.


- Awake fullsuite06 on identical source: **794passed in237.82seconds**. Actual
  streaming03 reached routed baseline15LUT/19FF,setup0.302ns; optimization pending.
  Publishing tested portfolio/typed-blocker source now; finalmainintegration still
  requires completed streaming checks and freshfulltier0, no higher held tier.


- Streaming03 completed atafcc080: combined generated+independent verification,
 15LUT/19FF baseline retained, setup0.302ns/hold0.138ns;5modelcalls,
 384.843chargedtoolseconds/435.038elapsed. Equal-area candidate also duplicated
 frozencompaniondefinition and was model-rejected. Independent saved-winner
 plus declaredchild passed; actual DONE replay kept42selected identities equal.
 Archive generated-streaming retains raw reports, grader misses and sources.
- Two observed gaps recorded in taxonomy before repair: journal omitted raw
 assertionTXT and DONE omitted qualificationJSON; exit-zero duplicate-module
 warnings were accepted by deterministic tool gates. Restored/hashed proof now
 survives replay, and exact VRFC10-3609/Synth8-9873 diagnostics reject DESIGN.
 Nonzero infrastructure failures retain precedence. Focus43tests and compiler
 focus24tests pass; exact old bad candidate now fails before elaboration.
 Read-only peer review approved freeze. Fullsuite07 running; main not merged.

- Final fullsuite07: **807passed in137.16seconds**. No runtime edits during tests.
  Publishing tested guards and streaming archive; freshfulltier0 campaign06 is
  next, required before main integration. No higher tier is held.


- Fresh campaign06 counter completed on frozen8098466: accepted **55 to31LUT
 (43.64%)**,37FF. Setupslack0.494to0.126ns; holdslack0.113to0.026ns, both positive.
 The extended increment adder shares carry with overflow; reset/load/enable and
 pre-edge registered flag behavior remain fixed. Independent default32bitTB,
 actual exit receipts, routed reports and final evaluator9/9 passed.3modelcalls,
 443.859chargedtoolseconds/469.442elapsed. A read-only arithmetic/priority review
 found no blocker for tested binary/default behavior; no all-parameter or X/Z
 equivalence claim. Actual DONE replay preserved76protected identities including
 budgets and winner. Mux still running; no fullcampaign or merge success yet.


- Fresh06 fulltier0 completed **2/2**, qualifiedstreak1/heldfalse. Mux equal-area
 candidate rejected;8LUT/8FF baseline retained,setup0.579/hold0.052ns;3calls,
 427.438chargedtoolseconds/450.888elapsed. Both entries match53committed runtime
 identities at8098466. No runtime edits occurred during campaign. No higher held
 tier or observed CLI model identity. First pre-run missing-PYTHONPATH traceback
 is retained separately; no task was created/charged before that import failure.
- Final portable campaign archive, source identity and hash manifests prepared;
 main integration is now authorized by passing full807tests plus freshfulltier0.
 Queue finished and temporary keep-awake flag removed. Next design's exact FIFO
 contract/matrix/fault admission plan is in docs/TASKS.md, not public README.


- Verified GitHub publication: main and codex/contract-context fast-forwarded
 atomically to **a113ca192085bd8406f734f66891a69e35216a99**. Local main updated
 with expected-old-ref check; remote heads confirmed identical. Runtime source
 remains8098466; only evidence/docs changed after the tests and campaign.
- No vendor processes remain. Temporary system-awake request confirmed released;
 power plan unchanged. Saved coordinator checkpoint retains progress, not a
 background job. Next concrete work is FIFO fixture/TB/mutation admission per
 TASKS; no extra framework, agent layer or weak-model claim was added.


## 2026-10-20 continuation: parameterized FIFO admission

- User confirmed own Vivado work will be code/testbench editing and simulation,
  with no synthesis/bitstream generation; authorized continuing harness work.
  Preserve separate folders and one serial harness vendor queue.
- Began reviewed WIDTH8/DEPTH3 synchronous FIFO contract with independent default
  wrapper and WIDTH/DEPTH corner matrix. Bounded fixture and runner workers own
  separate scopes. No generated build or hardware result is yet claimed.
- Read GateTruth and VeriBugBench primary papers; research ledger records the
  relevance and limits. Keep concrete fault provenance/raw assertions and report
  all planned outcomes. No framework, model role or automatic fault engine added.


- FIFO admission complete: real reference+13faults **14/14expected verdicts**.
  Six matrix controls each check701..771cycles; no compile/infra failure counts
  as a behavioral kill. Actual generated default payload scoreboard also passed
  the supervised reference. No qualification source/oracle is supplied as a model
  seed. Fullsuite **836passed in270.94seconds**, frozen runtime/fixture bytes.
  Publishing tested fixture/runner/research and exact evidence before model build.


- FIFO01 onffc15fc: functional checks and both qualifications passed; routed
 13LUT/6FF,setup-0.931ns/hold0.091ns, **timing not closed**. Candidate duplicated
 frozenchild and was correctly compile-blocked.4calls,226.360chargedtoolseconds,
 284.528elapsed. Independent saved-artifact matrix passed; physical failure is
 preserved. Same-SHA readiness mutant passes payload grader but fails matrix.
 Actual DONE nominal replay plus qualification-report tamper rejection preserved
 184selected identities after original bytes restored. No calls/tools rerun.
- Failure-driven corrections planned before hotfix in taxonomy/HARNESS_REVIEW:
 feasibility-first policy, explicit edit boundaries, bounded compile+sim repair.
 Purepolicy64tests and context26tests passed; integratedfocus172passed82.17s.
 Initialfocus168passed/2failed because oldfixtures encoded contradictory timing
 or expected a repair atbudgetzero; corrected truthful fixtures, all assertions
 retained. Compile/sim repairs now keep separate attempt sources/logs.
- Read-only peer review caught Windows Unicode source IO mismatch; two new tests
 reproduce it (candidate evidence compare and Doctor source write). It also found
 DONE omitted childRTL referenced by simulation manifests; tamper/delete and
 changed-before-finalization regressions are being added before the guard fix.
 No new physical success or relaxed timing constraint is claimed by these tests.


## 2026-10-21 continuation: recovery guard validation

- Resumed after automatic approval review was temporarily unavailable because
  of usage limits. No command was executed by that rejected request. Existing
  uncommitted changes and failure artifacts were preserved.
- Final integrated recovery focus: **187 passed in143.87seconds**. UTF8 source
  identity and original child-source retention now pass their before-failing
  regressions. Strict verification manifest version rejects bool/float values:
  **12 passed**. Read-only peer review found no remaining concrete blocker.
- Frozen fullsuite is running. Main integration and any new physical recovery
  remain unclaimed until actual fullsuite/freshcampaign evidence passes.

- Final frozen fullsuite: **939 passed in349.85seconds**. Prior fullsuite had
  938passes/one legacy synthetic cache fixture missing source/TB lineage; added
  truthful synthetic manifest without relaxing production gates or assertions,
  then20filetests passed and fullsuite rerun passed. Archived all outcomes.
- Publishing reviewed recovery source and failed FIFO01 evidence to development.
  Main remains7bef3bf until fresh fulltier0. FIFO02 uses a fresh run and the newly
  committed frozen runtime; no physical timing recovery is yet claimed.

- Published49599b5 verified on GitHub development; runtime55/55files match. FIFO02
  repaired oracle syntax and qualified both graders, then PC sleep/hibernate
  interrupted baseline synthesis. Receipt timed_out/driver124 despiteactualexit0;
  budget_exhausted with3calls,18741.826chargedtoolseconds/18775.798elapsed. No
  optimization/winner or physical result. Original budget retained; archive02
  preserves failure. FreshFIFO03 is a separate experiment on unchanged49599b5.
- Old helpers72074/72910 released. New bounded queue helper12596 active; remove
  verification flag after queue. No powerplan or user GUI/simulation changes.

- FIFO03 on frozen49599b5: baseline13LUT/6FF,setup-0.931/hold0.091ns.
  Candidate1 setup-0.905; Doctor-0.525stillinvalid/notadopted; candidate2-0.600.
  Second Doctor exact unchanged source reran and exhausted remaining tool time.
  Finalbudget_exhausted,10calls,1200.654chargedtoolseconds/1349.068elapsed; no
  saved finalwinner/acceptedphysicalresult. Archive03:295files,manifestverified.
- Evidence review identified reportpreview truncation beforepaths, lost resolved
  typed semantics, missing rejected-Doctor feedback and no-op surgery repeats.
  All four recorded in taxonomy before corrections. Existing fact/advisor/parser
  plumbing will carry bounded exact evidence; proven same-flow no-op skips only
  surgery, intentional physical experiments stillrun. No newrole/framework.

- Feedback changes implemented and read-only peerreview found no blocker.
  Context51tests pass2.81s; Doctor74pass212.77s. Removed test-only legacy parser
  inference; synthetic helper now supplies real path fields, assertions intact.
  Firstfullsuite984passed408.00s. Final no-op sourcepreview completion passed its
  targeted regression1test0.71s; finalfullsuite02 running on frozen source.
  New related trial/spec digests are protected against pre/postDONE mutation.

- Final feedback runtime fullsuite: **984passed423.26seconds**. All187 recorded
  runtime/test/curriculum identities unchanged during final run. Read-only peer
  review and focused51/74checks passed; original before/after failures preserved.
  Publishing complete tested source and both failed FIFO02/03 archives.
- FIFO04 predeclared budget:2iterations,1candidate,16calls,25toolminutes,
 35wallminutes,oneinfraretry. Larger time allowance covers two possible Doctor
  trials; no oldrun counters reset and no controlled efficiency comparison with
  earlier budgets or unobserved CLI model identity is claimed.

- Published feedback source **d39e34d**. FIFO04 completed on that frozen runtime:
  both graders qualified; retained baseline13LUT/6FF, WNS-0.931/WHS0.091ns.
  Candidate2 passed temporal matrix and routed setup/hold with24LUT/27FF,
  WNS0.318/WHS0.050ns, but reviewer rejected solely an invented required numeric
  top annotation despite authoritative declared_latency.known=false. Original
  rejection retained; no candidate regrading/promotion.9calls,872.439chargedtool
  seconds/978.931elapsed. Exact saved baseline+children independently passed.
  Archive generated-fifo-attempt-04 contains280verifiedfiles. This demonstrates
  timing-recovery potential with an area cost, not an accepted optimization.
- Recorded invented_top_latency_requirement in taxonomy BEFORE implementation.
  Plan: align actual injected conventions, evaluator and fixed evidence on the
  authoritative top declaration; inherit typed metadata only for mechanically
  proven transparent single-child wrappers. Arbitrary aggregate latency stays
  unknown; typed module and behavioral/setup/hold gates remain intact.
  Bounded workers own distinct files; fullsuite and fresh runs follow review.

- Wrapper focus38passed0.31s; conventions13passed1.06s; assembled latency policy
  focus91passed70.86s (actual injected conventions, build/standalone, known/
  unknown, six role entry points).
- Read-only review found a preexisting whole-file annotation search attributing
  helper-module/block-example metadata to the selected top. Recorded
  cross_module_latency_annotation before correction. Fullsuite01 was already
  running; recording this runtime taxonomy change invalidates its freeze, so
  its outcome will be retained as preliminary only. No source correction is
  made until it exits. A complete fresh final frozen rerun is required.

- Preliminary fullsuite01 exited0:1042passed301.43s; retained but not final
  freeze-qualified. Module parser100focusedpassed1.14s. New crossstage focus
  initially9pass/1fail: malformed annotation escaped comment-stripped static
  inference and raised. Passing originaltext into existing interface inference
  converts it to a static design failure. Full client/optimizer/Doctor/gate focus
  then66passed70.01s. Allfourselectedmodulecalls covered.
- Final fullsuite02 running frozen with175source/test/fixture identities.
  Old awakehelper12596 released; bounded helper80718 nowserves queue.

## 2026-10-22 continuation: tested latency correction

- Reconciled actual Git/processes; no old harness jobs running. Expired lease
  reclaimed; interrupted source preserved. Saved final fullsuite02 completed
  October21: **1074passed274.48seconds**. All175recorded source/test/fixture
  identities unchanged onOctober22. This is saved validation, not a new rerun.
- Final read-only parser/caller/static integration review found no blocker.
  Archived successful/failing focused and preliminary/final fullsuite outputs
  with source and archive manifests. Public README reflects1074tests.
- Publishing the complete latency-authority correction; FIFO04 remains a
  preserved rejected trial. FreshFIFO05 and fulltier0 still precede main merge.

- Published **85e4fb8**, GitHubdevelopmenthead verified; mainstill7bef3bf.
  All55runtimefiles match publishedfilteredGitblobs. Completed implementation
  claims with tested evidence. Fullsuite03 session29021 additionally verifies a
  trailingEOFblank cleanup in one test; no runtime behavior changed.
- Live power checks: CIMbattery0%discharging; kernelGetSystemPowerStatus
  AC0,Flags6(low+critical),Percent0,Saver1. Requested charger connection async.
  Prior actual sleep failure motivates holding new long Vivado jobs until AC
  is detected or user explains reading. Tests/docs/provenance work continues.

- Final publication fullsuite03: **1074passed344.74seconds** October22,
 175source/test/fixture identities unchanged. This is a fresh complete test,
  not reuse of prior output. Only change from suite02 is removed testEOFblank;
 all55runtimefiles remain85e4fb8. Archived03 plus original02 manifests/logs,
 updated README direct evidence link. No failed criterion was relaxed.

- Published final evidence **9cead4e**, GitHubdevelopment head verified; main
  remains7bef3bf because fresh physical/tier0 gates are pending. Worktree clean
  at publication. Second kernelpower check stillAC0/Flags6/0%; charger question
  unanswered. FIFO05/campaign07 notstarted, no reset budgets or claimedresults.
  Awakehelper1834 released cleanly after flag removal; no vendor/helper jobs
  left running. Shared memory records exact next command and power dependency.

## 2026-10-22 physical validation resumed

- Power nowcharging16%; no oldvendorjobs. Claimednewcoordinator/doc/evidence
  scopes and bounded awakehelper81495 forrealqueue.
- Started freshFIFO05 session57827 on published6f3fa7c/runtime85e4fb8.
  All55runtimefiles matchcommit. Predeclared3iterations/1candidate,16calls,
 25tool/35wallminutes,oneinfraretry,generatedgoldenplusfrozenindependentmatrix.
  Spec/TB/10ns/xc7a35tcpg236-1/Vivado2025.2unchanged. No oldrun resumed/regraded.

- FIFO05iter1:21LUT/26FF,WNS-.289ns; tool-onlyDoctor21LUT/27FF,-.016/.005ns
  remainedinvalid/notadopted. Annotationcriterionpassed; normaltimingrejection.
- FIFO05iter2 accepted **timing_recovery**:24LUT/14FF,WNS+.013/WHS+.027ns,
 7/7reviewPASS and selectedtemporalparameterchecksPASS. Higherresourcecost
  versus13LUT/6FFbaseline is recorded; notarea savings orboardtimingproof.
  Iter3currentlyattempts strictLUTreduction while retaining setup/holdfeasibility.
  This is an accepted intermediatebest, not yetfinalsavedwinner/DONEvalidation.

- FIFO05 DONEiter3 **22LUT/13FF,WNS+.108/WHS+.076ns** via boundedRTLDoctor
  registering equivalentvalidstate. Iter2firstfeasible24LUT→22LUT=8.33%reduction;
 baseline13LUTfailedtiming, sooverallresultistiming_recoverywithareacost.
 13calls,856.39chargedtoolseconds,1041.5565elapsedseconds. Finalreview5/5PASS.
- Exact savedwinner+declaredchildren separately passed independentmatrix.
  ActualDONE nominalreuse0; child/spec/Doctorreporttamper eachrejected1 then
  restored;327identities, fileset andbudgetunchanged, noextramodel/toolcharges.
  ArchiveFIFO05 manifestverified. All55runtimefiles stillmatchpublishedsource.
- Freshfulltier0campaign07 startedsession31889. Firstlaunchfailed before any
  run/model/tool because barePythoncouldnotimportyaml; originalconsole retained.
  Corrected launchenvironment toexistingreview_deps PYTHONPATH (no sourcechange,
  no dependencyinstallation); campaignnowrunning serially withpredeclaredbudget.

- Final read-only FIFO05 review found no blocker; verified registered valid-state
  invariant and tail-pointer transitions. Recorded source equivalence explicitly:
  measured stage uses CRLF, saved winner LF; full text equal after ONLY CRLF→LF,
  independent source_0 byte-identical to saved winner. Raw measured source and
  all actual hashes retained. Archive now369files including this hash link.

- Fresh fulltier0campaign07 **2/2PASS**, qualificationtrue, streak1, heldfalse.
  Counter55→31LUT(43.64%),37FF,WNS+.126/WHS+.026ns; baseline+.494/+.113ns.
 3calls,249.126toolseconds/272.556elapsed. CounteractualDONEreuse preserved80
  hashes/fileset/budget with no newcalls. Unknown latencycriterionpassed8/8review.
- Mux baseline8LUT/8FF,+.579/+.052ns retained. Initial primitive proposal failed
  xelab (unlinked MUXF7/MUXF8); boundedrepair passed then nogaincorrectlyrejected.
 4calls,187.781toolseconds/220.759elapsed. Actualfailure/repair botharchived.
- Campaignarchive210files verified; both55-file runtimeidentities matchsource
 6f3fa7c, governanceunchanged, all175finaltestedsource/fixtureidentities unchanged.
  Oldercohortsnotcounted; no weaker-model orall-parameterproofclaimed.
- User asked about independence and roles. Explained boundedCLI runs do not
  dependon this chat; genericapplication/continuousunattended supportrequires
  matchingtool/protocolverification and deploymentoperations. Existingroles
  were clarified and grounded, not expanded into moreagents. No newframework.
- Main integration gates nowpassed:1074tests, freshfulltier0, acceptedFIFO05,
  independentfinalwinner and actualDONEchecks. Preparing authorizedatomic
  fast-forward from7bef3bf; actualfinalheads recorded afterpush.

- Authorized atomic integration completed: **141c548** now verified on both
  GitHub main and development; localmainmatches andworktreeclean atintegration.
  Full1074tests andfresh2/2tier0 gates passed on unchangedruntime.
- User requested continued judgement and context safeguards. Clarified host
  compaction vs repository continuity: no custom token threshold configured.
  Added explicit verify-after-compaction rules to AGENTS/AGENT_HANDOFF, bounded
  historical reads and evidence-first checkpoint fields. No claim of immunity
  to reasoning errors. Starting reviewed packet-tag FIFO fixture next.

- Packet control-only real simulation passed allsixconfigurations,901..978
  checkedcycles; data/tagorder, markerconservation, fullboundarysimultaneous,
  stalls andoccupiedreset coveragepositive. No model orphysicalclaim.
- Packet integrationfocus60passed5.09s. All185source/test/fixture/guard
  identities frozen. Startedserial20case qualification12870 and complete
  pytest59811; no source edits untilbothfinish. Qualification compiles must
  succeed and faults must fail realbehavioral assertions; no timeoutaskill.

- Packet admission completed: fullsuite **1105passed288.12s**, integratedfocus
 60passed5.09s. Real20casequalification passed20/20: sixconfigurationcontrol
 and19behavioralassertiondetections, no compile/infra/watchdogkills. Bothjobs0.
 All185frozenidentities matched atcompletion. FollowupfixtureREADME only
 clarified measuredadmission and overlappingcapture/outputfaults; precise
 documentationhashdelta retained, executablefixture/tests/runtimeunchanged.
- Read-only packetcrossreview found no blocker. Archive packet-fifo-admission
 contains202manifestedfiles, verifiedhashes andrawverdicts. Kept existingroles,
 multioutputscoreboard andindependentqueue; no newruntimeframeworkmechanism.
- Fresh packet01 budget predeclared:3iterations/1candidate,16calls,25tool/
 35wallminutes,1infraretry,same10ns/device/toolchain. No referenceseed.
 Generatedgrader sidebandsensitivity andfinalsavedwinner/DONEchecks stillpending.
 Mainremains141c548 untilfreshfulltier0 gate; developmentmilestonewillbepushed.

- Development1357a08 pushed/remoteverified;mainstill141c548. Freshpacket01 session45225 launchedwithoriginalbudgets. All55runtimehashesmatchcommit. OracleSyntaxError rejected/repaired attempt2; generatedgrader caughtstuckzero aftermissingreadinessflip. No finalbuildclaimyet.

- Packet01 intermediate timingrecoveryacceptediter1:23LUT/31FF,WNS+.078/WHS+.106ns afterboundedtoolknobs. OriginalcandidateWNS-.172;baseline15LUT/6FF,WNS-.946/WHS+.167ns. Higherareaistimingrecovery,notareasavings. Iter2active;finalsavedwinnernotyetvalidated.

- Packet01 completed: best iteration1 retained at **23 LUTs/31 FFs,
  WNS +0.078 ns/WHS +0.106 ns**, timing_recovery from invalid15LUT/6FF,
  -0.946/+0.167ns baseline. Tool-knob trial closed initial shiftqueue's -0.172ns.
  13 model calls,769.639 charged tool seconds,937.551 elapsed seconds.
  Iter2 failed timing; iter3 was feasible27LUT/30FF,+.333/.115ns and correctly
  rejected for increased LUTs. Churn watchdog replanned but source repeated.
- Frozen generated grader separately passed control and caught all six named
  marker faults against original qualification hashes. No sideband engine gap
  found. Readiness fault remains missed by generated grader, caught independently.
- Exact savedwinner/declaredchild passed independent sixconfiguration matrix.
  Actual DONE nominal0 and temporary child/spec/Doctorreport tamper1 each;
  331 identities,fileset,budget restored unchanged,no extra model/tool charges.
  Measured CRLF/saved LF differ only line endings; identity link retained.
- Packet archive421 manifested files verified. Read-only final review found
  no blocker. No all-parameter/formal/board/weak-model proof is claimed.
  Started required fresh fulltier0 campaign08,session14413,1iteration/1candidate,
  16calls/20tool/30wallminutes/1infraretry perentry,same target/constraints.
  Main remains141c548 until campaign gate passes. All55 runtime files unchanged.

- Read-only next-stage source audit refined earlier causal wording: CHURN is printed and passed to planner, but need_plan directly checks initial/stall/periodic/STAGNATION. Packet iter3 replanned via scheduled/stall condition, not a direct CHURN trigger. Corrected summary README/review and its manifest; raw evidence unchanged. Concrete next study: bounded journaled previous-proposal instruction/source/outcome feedback, separate standard vs Doctor flow outcomes; retain repeated-source tool exploration. No runtime edits during campaign.

- Fresh fulltier0campaign08 completed **2/2 PASS, matching cohort streak2,
  heldfalse**. Counter55→53LUT/37FF,WNS+.456/WHS+.282ns,3calls; smaller gain
  than prior31LUT trial is retained honestly. Mux8LUT/8FF,+.579/.052ns baseline
  retained;8LUT no-gain proposal rejected,3calls. No primitive failure thisrun.
- Campaign archive195 files verified; both55-file runtime manifests unchanged,
  same known cohort9b69c8d0/governance. All executable/test/fixture identities
  still match1105-test freeze; fixtureREADME-only posttest delta documented.
  Admission202,packet421,campaign195 archive manifests all verified together.
- Regression/fulltier0/independent winner/actualDONE gates now passed for
  packet milestone. Preparing authorized main/dev integration; actual remote
  commit is recorded after push. No higher held tier or weak-model proof.

- Authorized atomic integration verified on GitHub main and development at **821afbe451d21501dd7581bad11ffbcdff19217b**. All required gates passed. Vendor/model queue empty; awakehelper81495 exited0 and released request. Documentation-only followup records actual publication. Localmain updated by expected-old ref; no user GUI touched. Next reviewed task is bounded previous-proposal feedback study, not untested role expansion.

- User clarified counter alreadycomplete and requested morecomplexdesigns. Explained counter/mux fresh runs are regressiongates, packet01 complete. Advanced to reviewed multi-cycle unsigned divider plan before implementation; default latency9/overrideWIDTH+1 exactschedule, q/r,div0,backpressure/reset. Existing scoreboard supports it; no newruntimeengine. IndependentTB worker never reads reference. Claimed nonoverlapping scopes; driver35focusedtests passed5.44s. No actual divider tool/modelresult yet. Proposalfeedbackstudy recorded, arithmetic prioritized peruser.

- Divider correctcontrol actualsim passed allsixwidths. Checked1613..3454cycles onshowncases; exhaustiveWIDTH1/2/4,highbits/div0/busy/resultstall/resetphasecoverage and transactionconservation passed. Control54167 finished0; no model/PPA/admissionclaim. Boundedawakehelper13973 active120min fordividerqueue. Await qualificationworkerfixturetests/freeze beforefull21casequalification/fullsuite.

- Dividerfixtureworker67tests passed3.50s; parentintegrated102passed5.51s. Read-only crossreview no blocker. All192source/test/fixture/guardidentities frozen; startedactual21casequalification69785 andfullsuite94856, no editsuntilbothfinish. Actualcontrol6widths passed1502..3454cycles. No model/PPAclaim.

- Divider admission01 REJECTED:20/21expected,correctcontrol+19assertiondetections; reset_preserves_held_result PASSED. Full1175tests passed188.39s andall192hashesmatched, but admission correctlyblockedmodelgeneration. Rootcause heldresetcaseout_ready1 allowedordinaryretirementtohideignoredreset; reset_resultcountdidnotdistinguishstalledabort. Original21rawcases/sourcefreeze/results archived BEFOREhotfix in evidence/2026-10-22/divider-admission-attempt-01. Existingcurriculumfault identifiesfailuremode beforecorrection. Keep originalmutant,adddistinctheldout_ready0resetcase+coverage+regression,thenfullrequalification/fullsuite.

- Preservedfailedadmission01archive212filesbeforefix. Addedstalledreset(out_ready0)case plusdedicatedcoverage; originalresettransfercasesretained. Tests72passed3.82s;parentintegrated107passed7.81s. ExactlyTB+fixturetestchanged, reference/spec/20faultsourcesunchanged. New192-identityfreeze02; qualification56557/fullsuite44361active. No editsuntilbothfinish; modelgenerationstillgated.

## October23: recovered divider admission and advanced model stage

- Recovered actual fullsuite02:1180passed429.28s. Qualification02 passed21/21,
  correctcontrol+20behavioralassertions; stalled-reset fault now detected.
  All192 frozen identities unchanged. No owned tool jobs remained; expired
  coordinator lease reclaimed after process/Git audit.
- Successful admission archive199files verified, with identical reference and
  allmutant hashes versus failed01. Original212-file failed archive retained.
  No weakened contract or substituted mutant. Fresh model budget remains
 3iterations/1candidate,16calls,25tool/35wallminutes,1infraretry; no reference seed.
- Condensed current recovery notes to current facts/nextcommand; historical
  evidence remains in PROGRESS and Git. No custom compaction threshold claimed.

- Published fixture cfef8af todevelopment afterreview,1180fulltests/21of21admission. Freshdivider01 modeljob66886 launchedwithoriginal3iteration/16call/25tool/35wallbudget. All55runtimehashesmatchlaunchcommit. Awakehelper55214 activebounded120min; onevendorqueue. No reference seed or generatedPPAclaim.

- Divider01 baseline passes dualgraders/independentwidthmatrix androuting:38LUT/46FF,WNS+.324/WHS+.136ns. Oraclefirstattemptdivmod rejectedbyallowlist, repairedattempt2; bothgraderscaughtflip==to!=. Iter1optimizesstrictLUTfromfeasiblebaseline; noacceptedimprovementclaimyet. Originalsource/budgetsunchanged.

- Divider01 DONE bestiter3 **26LUT/38FF,WNS+.315/WHS+.129ns**, baseline
 38LUT/46FF,+.324/.136ns; accepted31.58%LUT objective improvement. Iter1 won
 30LUT/39FF,iter2 duplicated/rejected via cache,scheduled/stall replan received
 churn and proposed shared subtract,iter3won.11calls,409.939chargedtoolseconds,
 560.999elapsedseconds. Estimatedpower increased.092->.103W,notpowergain.
- Exactsavedwinner/declaredchild independentmatrixPASS. ActualDONE nominal0,
 child/spec tamper1 each,251hashes/fileset/budget restored,noextra calls/tools.
 Read-only source/report review found no blocker; actual8steprestoringtop.
 MeasuredCRLF/savedLF complete normalizedtexts equal,independentcopybyteequal.
- Supplementalfrozengrader13/17applicablefaults; missedzero-divisorRzero,
 retirementedge ready,asyncreset,heldreset. Threewidth-onlyfaultsinapplicableat8
 excluded. Controlpassed; allfaultsourcehasheslinkedto21/21independentqualification.
 Archive436files verified BEFOREnextchange; original01neverresumed/regraded.
- Foundspecaccepted255/0=>R255 absentfromRTLstimulus,only0/0simulated.
 Independentplanreviewapprovedsmallscoreboardpayloadseedcorrection; claim
 scoreboard-example-inputs/Codex/scoreboard on tbgen.py/newtests. No newrole
 orengine, nofixed-latencytracechanges. Oldruntime results stayfrozen; newfull
 regression/controlledgraderexperiment/freshfulltier0 requiredbeforemainmerge.
