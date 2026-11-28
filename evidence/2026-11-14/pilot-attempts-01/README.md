# VerilogEval pilot attempts 01–03 and the clockless-timing fix — November 14, 2026

Pilot attempts that stopped on adapter or harness defects. None is a benchmark
result. Cells were never rerun inside an attempt; each fix got a taxonomy entry
and a new frozen attempt. Workspaces: `C:/Users/prince.baah/autortl-private/
pilot-0N` (outside the repository). `aborted_attempts.json` holds each
attempt's runtime identity, manifest hash and every sealed cell's receipt ID,
termination, accounting and run summary.

| Attempt | Runtime | Outcome | Defect (taxonomy) |
|---|---|---|---|
| pilot-01 | 62bfa818 | arm A ringer sealed; arm C stopped in 1.5 s | run.py rejects `--iterations 0` (`pilot_runner_double_hid_cli_rejection`) |
| pilot-02 | 8a50a8ab | 3 arm A sealed; 3 arm C stopped in ~24 s | bare `xvlog` cannot start a .bat (`pilot_vivado_tools_unresolved`) |
| pilot-03 | b6f1cb4a | 5 arm A sealed; arm C: 2 combinational baselines blocked by the metrics gate, circuit10 spec repair returned partial JSON, count15 DONE but sealed interrupted; stopped before m2014_q6b/fsm1s arm C finished | `clockless_design_untimed_by_metrics_gate`, `pilot_submission_missing_children`, `pilot_outer_timeout_discarded_done` |

pilot-03 also showed host sleep: count15's synthesis started 11:28 and its
reports were written 17:56–17:58. The harness classified the stalled synthesis
as infrastructure and retried; the session now holds a keep-awake request.

## Clockless timing fix, live check

`combinational_timing.json`: Prob036_ringer's reference (renamed TopModule)
through `autortl.vivado.run_synthesis` on Vivado 2025.2, xc7a35tcpg236-1, 10 ns,
after the virtual-clock change. Both flows time the input-to-output paths and
pass the unchanged metrics gate: out_of_context WNS 7.905 / WHS 0.840 ns, 2
LUTs; chip_top WNS 3.194 / WHS 2.019 ns, 1 LUT. Before the change both values
were -999 and the gate stopped the baseline.

## Arm C end-to-end check (not a sealed result)

Prob038_count15 pilot-03 arm C output, assembled with the corrected
`submission_files` (verified child `modules/TopModule/TopModule.v` + winning
`TopModule_top_best.v`) and graded against the official testbench with Icarus
12.0: strict pass, upstream `.`, 0 mismatches in 421 samples. It was sealed
interrupted in pilot-03 and is reported here only as an adapter check.
