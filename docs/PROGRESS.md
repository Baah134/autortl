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
