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
