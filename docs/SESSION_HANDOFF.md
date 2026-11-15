# AutoRTL current checkpoint

## Current — November 14, 2026 (late): pilot gate passed, final run ready

Coordinator: Claude. Branch `codex/contract-context` at 775820583 (local, not
pushed). pilot-06 (runtime e61a09827) passed the gate: single_call, ablation and
full each 6/6, every cell done (evidence/2026-11-14/pilot-06-results-01). pilot-05
was aborted on a hold-exclusion defect, fixed in e61a09827. The final 40-task
registration is frozen (evidence/2026-11-14/final-registration-01, selection
c85666ff).

Final comparison prepared, not launched: `C:/Users/prince.baah/autortl-private/
final-01/manifest.json` (360 cells: 40 tasks x 3 arms x 3 trials, runtime
775820583) and `final-01/run_all.sh` (trial-major; never reruns a cell). Launch:
`bash C:/Users/prince.baah/autortl-private/final-01/run_all.sh <venv python>`
from any shell; grade only after all cells are sealed with
`autortl-private/grade_pilot.py <repo> <final-01> <dataset> <iverilog> <vvp>`.
Expected from pilot-06 rates: about 19 h awake time, about 1,700 Codex calls and
40M input tokens (much of it cached). The host must not sleep.

Open: `planner_spec_error_shared_by_oracle_and_rtl` (not reproduced in pilot-06),
no push yet, main still frozen at ca61dbc.

## Earlier — November 14, 2026 (evening): pilot-04 graded, workers merged

Coordinator: Claude. Branch `codex/contract-context` (local commits since
b98b6c4, not pushed). VerilogEval c498220 at `C:/Users/prince.baah/autortl-private/
verilog-eval`; pilot workspaces `autortl-private/pilot-0N`; Icarus 12.0 (MSYS2).

- **pilot-04 graded** (runtime 2f06f206): arm A 6/6, arm C 4/6 with one false
  acceptance (Prob135_m2014_q6b, planner spec error shared by oracle and RTL).
  Evidence `evidence/2026-11-14/pilot-04-results-01`.
- **Merged worker branches** (each reviewed, built in its own worktree off
  2f06f206): triage of unstartable tools as infra; arm B
  `--verification-policy skip_generated_tb_mutations`; `benchmark/registration.py`
  (40-task quota selection, exclusions file); resetless sequential modules
  (`reset: null` + `init_cycles`/`init_inputs`).
- **Coordinator fixes:** pilot `ablation` arm; out-of-context port timing for
  designs without a register-to-register path (input hold excluded; advisory
  QoR report skipped there after it crashed Vivado); Vivado crash banner
  classified as infra. Live checks in `evidence/2026-11-14/ooc-port-timing-01`.
- **Catalog:** two-reviewer adjudicated (kappa 0.962), 106 families
  (`evidence/2026-11-14/catalog-review-01`). Final selection (40 tasks,
  quotas 21/3/10/6) is computed but not yet registered.

Exact next action: after the full suites pass, commit; freeze pilot-05 (three
arms x 6 pilot tasks = 18 cells) on the merged runtime, run, grade; then freeze
the final registration and run the 40-task comparison (3 arms x 3 trials).
Open: `planner_spec_error_shared_by_oracle_and_rtl` (no mitigation adopted),
roles.py does not yet describe init_cycles to the golden/RTL writers, and the
machine's sleep stalls long runs (keep it awake or plugged in, lid open).

## Earlier — November 14, 2026: shortest path to the VerilogEval pilot

Coordinator: Claude (user-directed, November 14). Codex's November 13 lease had
expired; no repository file had changed on November 14 and no Vivado, xsim or
harness process was running. Codex desktop app processes started 08:06 were
present but no project job was attributable to them. Lease claimed normally,
without takeover. Branch `codex/contract-context`, base `b98b6c4`.

### User decision

Prioritise reaching the public benchmark pilot (ACTION_PLAN order 4/5) over
further export plumbing. The pilot validates adapter, grader, accounting and
budgets on six disjoint tasks excluded from results. Items only the final
registration needs are not prerequisites for the pilot.

### Plan (see ACTION_PLAN "November14 shortest path to the pilot")

0. Park the November 13 candidate-export stage (below) untouched. The pilot
   runs one job at a time, so it needs no run lock, and it takes each run's
   final selected RTL from the run directory instead of full snapshot history.
1. Pin VerilogEval spec-to-RTL to a full commit outside model-visible paths;
   record licence and per-file SHA-256; select six pilot tasks with the Nov6
   hash rule across the four categories.
2. Grader: Icarus v12 (install needs user approval: MSYS2 or WSL) wrapped by
   `benchmark/verilogeval.py`, matching upstream compile/30 s simulation
   semantics, recording real exits and mismatch counts. Controls: reference
   passes, broken copy fails, syntax error is compile_error, hang times out.
3. Arm runners in `benchmark/pilot.py`: A = one backend invocation; C =
   `run.py build --spec <prompt> --top TopModule --generate-golden` with the
   Nov6 provisional budgets. Arm B (mutation-qualification ablation) is
   deferred until before final registration. Seal with benchmark.artifacts.
4. Run 6 tasks x arms A,C x 1 trial = 12 sequential runs; grade only after
   every run is sealed. Check Codex quota headroom first.
5. Record adapter defects; tune budgets/prompts on pilot tasks only; freeze.

Final-registration-only items: OS-level hidden-grader isolation (pilot discloses
that it is not enforced), arm B seam, failed-call cost accounting, 40-task
roster and exclusion table, candidate bundles/run lock if jobs run in parallel.

Open user questions: Icarus via MSYS2 or WSL; whether arm C runs synthesis for
a functional benchmark; best_of_n 4 (default) or 1 (Nov6 proposal).

### Implemented this session (committed fb928002c)

Steps 2 and 3 code, with synthetic fixtures and process doubles only:
`benchmark/verilogeval.py` (task loading, Nov6 hash-rule pilot selection,
artifacts manifest, Icarus grader and summary parser), `benchmark/pilot.py`
(arm A/C runners, grading of sealed receipts, CLI),
`tests/test_benchmark_verilogeval.py`, `tests/test_benchmark_pilot.py`,
`tests/fixtures/verilogeval/` and the runbook `docs/BENCHMARK_PILOT.md`. No
harness runtime file changed. Full suites (scratch venv, Python 3.14, pytest
9.2): harness 2208 passed, 2 skipped (Windows symlink privilege; Icarus not
installed); tooling 323 passed, 1 skipped (symlink privilege). Tier bench not
rerun: no runtime change, and finished tiers are not re-held mid-development.

### Pinned, controlled and selected (user approved downloads, Nov14)

VerilogEval c498220d0a52 cloned to `C:/Users/prince.baah/autortl-private/
verilog-eval`; Icarus 12.0 installed via MSYS2. Upstream flags and analyzer
confirmed and ported (`upstream_passfail`, recorded beside the strict status).
Grader controls 16/16; reference sweep 152/156 with four dataset defects
excluded. One-reviewer catalog committed-to-be at
`benchmark/catalogs/verilogeval-c498220.json`; pilot (fixed slots 1/1/2/2):
Prob036_ringer, Prob033_ece241_2014_q1c, Prob147_circuit10, Prob038_count15,
Prob135_m2014_q6b, Prob107_fsm1s. Evidence:
`evidence/2026-11-14/pilot-grader-controls-01/`. A session lease lapsed once
mid-work (no other owner); it was reclaimed normally and scopes re-claimed.

### Exact next action

1. User: approve the commit (includes Codex's preserved taxonomy/
   HARNESS_REVIEW/TASKS acceptance notes) and answer arm C settings
   (synthesis on/off; best_of_n 4 or 1).
2. Commit; `python -m benchmark.pilot manifest --dataset <D> --commit c498220d0a52248f8e3fdffe279075215bde2da6 --tasks <6 IDs> --runtime-sha256 <hash> --out <outside-repo>/manifest.json`.
3. Check Codex quota; run the 12 cells sequentially per docs/BENCHMARK_PILOT.md;
   grade only after all are sealed.

Full suites after these changes (Icarus on PATH): harness 2226 passed, 1 skipped (symlink privilege); tooling 323 passed, 1 skipped.
No model, vendor or board job has run in this session.

## Paused — November 13, 2026: candidate-export implementation (Codex)

Canonical checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
Branch: `codex/contract-context`; last published commit:
`b98b6c4f82035144cb0c1e09ffc0126edaa36db2`. Main remains
`ca61dbcb6620914c8928c460d9aaf92aca608183` pending final release validation.
The separate `Downloads/autortl` copy must remain untouched.

### Actual state

The November 8 candidate-export session stopped at a usage limit before its
implementation stage was created. Only acceptance/taxonomy changes survived
in data/taxonomy.yaml, docs/TASKS.md and docs/HARNESS_REVIEW.md. These were
preserved. On November 13, Git still showed b98b6c4 and no live project jobs;
the expired coordinator lease was normally reclaimed without takeover.

Current work is staged under workspace `work/nov13-candidate-bundle-stage`.
Worker candidate_export_nov13_stage implements it; independent worker
candidate_export_nov13_review checks exact hooks, resume and export integrity.
Canonical runtime code is not yet integrated. No model/vendor/board jobs run.
The active coordinator is Codex; query SQLite ownership before editing.
Workspace root: `C:/Users/prince.baah/Documents/Codex/2026-10-15/hey`.

### Scope and exact next action

1. Review staged candidate_bundles.py, FSM hooks and benchmark/submissions.py,
   their real FSM/process controls, raw logs and exact final source hashes.
   Parent integrates only after independent approval and focused test success.
2. Record ordered complete source snapshots at every materialization, including
   raw best-of-N replies before later calls can block, repairs and Doctor RTL
   rejected by early static gates. Separate replay-safe generation and accepted
   incumbent decisions; never reset a later incumbent during baseline replay.
3. Add a small cooperative OS file lock shared by public Orchestrator.run and
   export. There was no existing run mutex: checkpoint replacement contention
   is different. The lock persists on disk, excludes concurrent access, and is
   released by the OS after process death. Prove this with actual child processes.
4. Bind the export to frozen runtime/config/requested model/budgets and exact
   run termination. Preserve unknown served-model identity and source-commit
   registration limits. Full verification only; no fabricated ablation or
   single-call acceptance. No catalog on a legacy run means unavailable.
5. Freeze integrated inputs, run full software suites, archive exact evidence,
   audit committed bytes and push development. Verify Git/remote/CI and update
   this single checkpoint. Do not duplicate jobs or modify frozen sources.

Acceptance: workspace work/nov8-candidate-bundle-acceptance.md, with the
run-lock correction also recorded in TASKS/HARNESS_REVIEW/taxonomy. Latest
published seam review: evidence/2026-11-08/benchmark-artifacts-01/
nov8-benchmark-next-review.md. No candidate export result is claimed yet.

### Previous measured results and limits

Published b98b6c4: 2,171 harness and 323 tooling passes, two Windows privilege
skips, 347 unchanged frozen inputs, committed audit passed, 283 new archive
files verified, and CI run42530896878 succeeded. The artifact API supplies
strict manifests, public-only exports and externally anchored RTL seals.
It does not yet select FSM candidates, execute arms, grade RTL or prove
OS/network isolation. No public tasks have been selected or scored.

AES04 is closed: controller qualified; round oracle qualified on attempt3;
all four round RTL candidates failed102 assertions. All343 original inputs
and219 run archive entries were verified. No integration/PPA/hold/board
success followed. No AES05 or further AES-specific prompt tuning. The missing
expected/actual repair diagnostics remain a separately recorded general
limitation, not a measured fix. Old tier holds belong to their original runtime.

### Recovery and safety

Coordinators take turns; follow AGENTS.md and docs/AGENT_HANDOFF.md, inspect
actual jobs and dirty files, and claim exact scopes. Do not reset/clean/stash,
switch branches, overwrite evidence, resume spent experiments on new runtime,
terminate unfamiliar jobs or publish tokens. Old campaign14/mailbox merge
requests are superseded. Checkpointing retains ownership; handoff is for a
real switch. These files do not schedule future execution or provider changes.

Main stays frozen until the final release validation/rehold. Do not repeatedly
rehold completed tiers during development. The connected Basys3 is outside
this stage: no JTAG, serial, programming, flash, reset or hardware-server calls.
Keep history in PROGRESS and Git; keep the README focused on public results.
