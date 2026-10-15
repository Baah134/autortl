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

## CV evidence policy

Record failures as well as successes. Quantitative claims require matching
source hashes, testbench, device, constraints, tool version, and baseline
and candidate reports. Document seeds, budgets, and number of trials for
autonomy claims. A passing startup check is not an autonomous design result.

For each future entry record: objective, user decision, branch/commit,
changes, commands, outcomes, evidence locations, limitations, and next action.
