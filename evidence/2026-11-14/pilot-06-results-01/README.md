# VerilogEval pilot-06 results — November 14, 2026 (pilot gate)

Pilot only: six tasks excluded from final results, three arms, one trial each.
Runtime `e61a09827` (`runtime-identity.txt`), manifest `benchmark_registration.json` (the frozen benchmark manifest; its file hashes refer to the external VerilogEval checkout, not to this folder), dataset
NVlabs/verilog-eval c498220d0a52, Codex CLI 0.167 (requested model: unobserved
CLI default), Vivado 2025.2, Icarus 12.0. Arms B and C: best_of_n 1, one
iteration, out_of_context, 16 calls / 25 tool-min / 35 wall-min. Every run was
sealed before grading against the official testbench and reference.

| Arm | Pass (upstream and strict agree) | Model calls | Input tokens | Wall time |
|---|---|---|---|---|
| A single_call | 6/6 | 6 | 61,846 | 42 s |
| B ablation (no generated-TB mutation qualification) | 6/6 | 40 | 972,111 | 28 min |
| C full | 6/6 | 40 | 971,278 | 28 min |

Every cell terminated `done`; no infrastructure stop, adapter defect or grader
disagreement. Prob147_circuit10 (no reset in the request) now builds with the
typed resetless form in both harness arms. Prob135_m2014_q6b, a false
acceptance in pilot-04, passed in both harness arms here: the planner spec error
was not reproduced, so the risk (`planner_spec_error_shared_by_oracle_and_rtl`)
remains open rather than fixed. The machine stayed awake throughout.

Pilot gate: adapter, grader, sealing, accounting and all three arms work end to
end on the frozen runtime. These numbers are not benchmark results.
