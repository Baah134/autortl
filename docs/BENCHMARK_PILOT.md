# VerilogEval pilot runbook

Pilot only: six disjoint tasks, arms A (`single_call`) and C (`full`), one trial
each. Pilot numbers validate the adapter, grader, accounting and budgets; they
are not benchmark results and are never pooled with final cells. Protocol:
`evidence/2026-11-06/parallel-diagnoses-01/nov6-benchmark-protocol.md`; plan:
ACTION_PLAN "November14 shortest path to the pilot".

Code: `benchmark/verilogeval.py` (dataset, selection, manifest, Icarus grader)
and `benchmark/pilot.py` (arm runners, grading, CLI). Standard library only.

## Pinned state (November 14)

- Dataset: NVlabs/verilog-eval `c498220d0a52248f8e3fdffe279075215bde2da6`,
  `dataset_spec-to-rtl` (156 tasks), cloned to
  `C:/Users/prince.baah/autortl-private/verilog-eval` (outside the repository).
- Icarus Verilog 12.0 at `C:/msys64/ucrt64/bin/{iverilog,vvp}.exe` (MSYS2);
  set `AUTORTL_IVERILOG`/`AUTORTL_VVP` or put that folder on PATH.
- Upstream flags, `timeout 30`/`TIMEOUT` handling and the analyzer's
  classification are confirmed against the pinned commit; the analyzer is
  ported as `upstream_passfail`.
- Grader controls: 16/16 as expected; reference sweep 152/156. Excluded for
  broken official references: Prob082_lfsr32, Prob141_count_clock,
  Prob156_review2015_fancytimer (testbench watchdog prints TIMEOUT for the
  reference) and Prob099_m2014_q6c (testbench/reference port mismatch).
- Catalog: `benchmark/catalogs/verilogeval-c498220.json` (one reviewer;
  second review pending before final selection).
- Pilot tasks (`PILOT_SLOTS` 1/1/2/2): Prob036_ringer, Prob033_ece241_2014_q1c,
  Prob147_circuit10, Prob038_count15, Prob135_m2014_q6b, Prob107_fsm1s.
- Evidence: `evidence/2026-11-14/pilot-grader-controls-01/`.

## What each arm does

| Arm | Generation | Submission |
|---|---|---|
| `single_call` | One `llm.client.ask("generator", prompt)` under a one-call budget; a timeout cannot become a second attempt | Extracted `TopModule` sealed `unverified`/`latest_complete`; otherwise missing (`model_blocked`, `budget`, `failed`) |
| `full` | `run.py build --spec <prompt> --top TopModule --generate-golden` with declared budgets in a fresh directory | DONE winner (plus verified children for frozen_children builds) sealed `accepted`/`accepted_incumbent`; otherwise missing |
| `ablation` | Same as `full` plus `--verification-policy skip_generated_tb_mutations` (skips only generated-testbench mutation qualification; recorded in events and summary) | Same as `full` |

Both arms receive the same public prompt bytes, checked against the frozen
manifest. The official `_test.sv`/`_ref.sv` are private manifest files; they
are never passed as `--tb` or shown to a model.

## Steps

1. **Pin the dataset** — done (see Pinned state).
2. **Classify and select** — done with a one-reviewer catalog:
   `python -m benchmark.pilot select --catalog benchmark/catalogs/verilogeval-c498220.json --commit <SHA> --out pilot.json`.
   Pilot families are excluded from final selection.
3. **Grader controls** — done: 16 per-category controls and a 156-task
   reference sweep; real Icarus logs replaced the synthetic parser fixtures.
4. **Freeze the manifest.**
   `python -m benchmark.pilot manifest --dataset <D> --commit <SHA> --tasks <6 IDs> --runtime-sha256 <hash> --out manifest.json`
   (refuses to overwrite). Commit the harness first: source/runtime commit is
   `git HEAD`.
5. **Run 12 cells sequentially**, each into a fresh directory:
   `python -m benchmark.pilot run --manifest manifest.json --dataset <D> --task <ID> --arm single_call|full --out runs/<ID>-<arm>-0`.
   Check Codex quota first. Do not rerun a cell into its old directory.
6. **Grade after all 12 are sealed**:
   `python -m benchmark.pilot grade --manifest manifest.json --dataset <D> --run runs/<cell> --out grades/<cell>`.
   Nothing is sent back to generation.
7. **Review**: adapter defects, statuses, calls/tokens/time per arm; tune
   budgets/prompts on pilot tasks only; freeze for registration.

## Grader semantics

`iverilog -Wall -Winfloop -Wno-timescale -g2012 -s tb -o sim.vvp <candidate> <test> <ref>`
then `vvp -n sim.vvp` under 30 s. Each verdict carries two classifications:

- `upstream_code`/`upstream_pass`: the pinned analyzer's code over the combined
  compile + simulation log (+ `TIMEOUT`) and the candidate source. Only `.`
  passes. This is the official-compatible functional endpoint.
- `status`: strict, from real exits: `pass` needs exit 0 and a final
  `Mismatches: 0 in M samples` with M > 0; a printed summary never overrides a
  nonzero exit or timeout. Values: pass, fail, compile_error, runtime_error,
  timeout, no_result, plus `missing` for a sealed missing record.

`agree` records whether both say pass or both say not-pass; disagreements are
reported, never resolved silently. A simulator that cannot start raises
`GraderUnavailable`: infrastructure, never a verdict.

## Known pilot limits

- Hidden-grader isolation is not enforced at OS level: the test files sit on
  the same disk as the Codex worker. Required before final registration.
- A `full` run without a DONE winner is recorded missing even if it produced a
  complete candidate; latest-complete selection needs candidate bundles.
- Arm C runs synthesis and routing; whether a functional benchmark should is an
  open user decision. `--best-of-n` and `--iterations` can be set per run.
- `single_call` declares a nominal one tool-second because artifacts require a
  positive value; it uses no tools.
- Failed or retried model calls inside arm C are counted by the run's own
  budget file only; full failed-call cost accounting is deferred.

## Arm C pilot settings (November 14)

`FULL_SETTINGS`: `--best-of-n 1 --iterations 1 --implementation out_of_context`.
VerilogEval grades function only and RTL optimization cannot change function
under a fixed contract, so arm C uses the minimum optimization (run.py rejects
zero iterations). Out-of-context implementation avoids board pin-capacity stops
unrelated to function. Runs need `AUTORTL_CODEX_BIN` (Codex desktop CLI) and an
interpreter with pyyaml.

## Pilot attempts

- **pilot-01 (aborted, adapter defect).** Manifest frozen at 62bfa818. Arm A
  on Prob036_ringer sealed a candidate (1 call, 7 s). Arm C on the same task
  passed `--iterations 0`, which run.py rejects; the run ended in 1.5 s with no
  summary and was sealed missing (`interrupted`). Taxonomy
  `pilot_runner_double_hid_cli_rejection`; a test now executes the real run.py
  parser. Both cells are retained in `autortl-private/pilot-01` and are not
  rerun; the remaining ten were never started.
- **pilot-02 (aborted, infrastructure).** Frozen at 8a50a8ab. Arm A sealed
  candidates for ringer, ece241_2014_q1c and circuit10. Arm C stopped in ~24 s
  on each with `xvlog not found` (bare tool names; taxonomy
  `pilot_vivado_tools_unresolved`), sealed `failed` because the harness reported
  failure_kind unknown. Batch stopped after the third arm C cell; its process
  tree had already exited. These infrastructure stops are not design verdicts.
- **pilot-03 (stopped, harness and adapter defects).** Frozen at b6f1cb4a.
  Combinational arm C baselines were blocked by the metrics gate (no clock, no
  timing: `clockless_design_untimed_by_metrics_gate`, fixed in
  `autortl/vivado.py`); circuit10's planner repair returned partial spec JSON
  (genuine failure); count15 reached DONE but was sealed interrupted by the
  sleep-counting outer timeout and its submission lacked the frozen child
  (`pilot_outer_timeout_discarded_done`, `pilot_submission_missing_children`).
  Stopped before the last two arm C cells. Evidence:
  `evidence/2026-11-14/pilot-attempts-01/`.
- **pilot-04 (complete).** Frozen at 2f06f206; 12 cells graded. Arm A 6/6
  (6 calls); arm C 4/6 (36 calls, about 13x the input tokens, 5-17 min per
  task). Prob135_m2014_q6b arm C was internally accepted but fails the official
  test (6/100): the planner misderived the spec and oracle and RTL shared the
  error (`planner_spec_error_shared_by_oracle_and_rtl`, open). Prob147_circuit10
  arm C was blocked by an untimed single-register design
  (`single_register_design_untimed_ooc`, fixed) after the planner added a reset
  port the request lacks (`resetless_sequential_unrepresentable`, fixed).
  Evidence: `evidence/2026-11-14/pilot-04-results-01/`.
- **pilot-05 (next).** Three arms (single_call, ablation, full) on the merged
  runtime: resetless modules, arm B seam, out-of-context port timing, triage.
