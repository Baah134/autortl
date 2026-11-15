# VerilogEval pilot-04 results — November 14, 2026

Pilot only: six tasks excluded from final results, arms A (`single_call`, one
backend invocation) and C (`full`, `run.py build`), one trial each. Pilot numbers
validate the pipeline; they are not benchmark results and are never pooled.

Identity: runtime `2f06f2063` (`runtime-identity.txt`), manifest
`benchmark_registration.json` (the frozen benchmark manifest; its file hashes refer to the external VerilogEval checkout, not to this folder), dataset NVlabs/verilog-eval c498220d0a52, Codex CLI 0.167
(requested model: unobserved CLI default), Vivado 2025.2, Icarus 12.0. Arm C:
best_of_n 1, one iteration, out_of_context, 16 calls / 25 tool-min / 35 wall-min.
Every run was sealed before grading against the official testbench and
reference (`summary.json`, per-cell `cells.json`, sealed RTL in `rtl/`; home
paths are replaced by `<home>`).

| Task | Category | Arm A | Arm C | Arm C calls / input tokens / s |
|---|---|---|---|---|
| Prob036_ringer | comb. logic | pass 0/19 | pass 0/19 | 7 / 184,843 / 310 |
| Prob033_ece241_2014_q1c | comb. arithmetic | pass 0/116 | pass 0/116 | 7 / 167,127 / 289 |
| Prob147_circuit10 | sequential | pass 0/232 | missing (baseline_blocked, infra) | 5 / 63,237 / 7,133 |
| Prob038_count15 | sequential | pass 0/421 | pass 0/421 | 6 / 137,086 / 1,001 |
| Prob135_m2014_q6b | FSM | pass 0/100 | **fail 6/100, internally accepted** | 5 / 101,851 / 889 |
| Prob107_fsm1s | FSM | pass 0/230 | pass 0/230 | 6 / 144,564 / 693 |

Arm A: 6/6, 6 calls, about 10,200 input tokens and 6–14 s per task. Arm C: 4/6,
36 calls, about 13x the input tokens and 5–17 min per task. Upstream and strict
classifications agree on every graded cell.

## Findings

1. **False acceptance (Prob135_m2014_q6b).** The planner derived the next-state
   table wrongly (state D, w=0 gives Y1=1; the request's D--0-->F gives 0;
   `m2014_q6b_full_design_spec.json`). The generated golden model and the RTL
   both implemented the wrong spec and its three examples avoided the case, so
   internal verification accepted a design the official testbench rejects.
   Taxonomy `planner_spec_error_shared_by_oracle_and_rtl` (open).
2. **Resetless interface (Prob147_circuit10).** The request has no reset; the
   planner added an `rst` port to satisfy the harness, changing the interface
   (taxonomy `resetless_sequential_unrepresentable`, fixed after this run).
3. **Untimed single-register design (Prob147_circuit10).** Its baseline was
   blocked by the metrics gate: out-of-context ports are untimed and the design
   has no register-to-register path, so nothing is timed (taxonomy
   `single_register_design_untimed_ooc`, fixed after this run). The machine also
   slept during this cell (18:37–20:30); the harness classified the stalled
   synthesis as infrastructure and retried.

On these six easy tasks a single call already succeeds; the pilot does not show
an advantage for the full harness, and it shows its first measured false
acceptance. The comparison on the registered 40 tasks, with arm B, decides.
