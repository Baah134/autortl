# Empty netlists, path-free designs and the final-01 abort — November 15, 2026

No model output is graded here. Tool controls on official VerilogEval c498220
references (RefModule renamed TopModule), Vivado 2025.2, xc7a35tcpg236-1, 10 ns,
through `autortl.vivado.run_synthesis` and the unchanged metrics gate.

## Why final-01 was stopped

`final-01_aborted_cells.json`: the registered comparison (runtime 77582058) was
stopped after 5 of 360 cells. Both single-call cells sealed candidates. The
three harness cells (vector1 ablation, vector4 ablation and full) ended
`baseline_failed`: these wiring-only designs synthesize to zero primitive cells,
the out-of-context placer reports "[Place 30-494] The design is empty", and the
harness treated that as a design failure and entered the repair loop. The cells
are retained, not rerun and not reported as results.

## Fix and live checks (`live_checks.json`)

| Design | Kind | Flow | WNS / WHS (ns) | Result |
|---|---|---|---|---|
| Prob015_vector1, Prob042_vector4 | wiring only, 0 cells | out of context | 9.002 / 0.385 | pass; place and route skipped |
| Prob002_m2014_q4i | constant output, no timing path | both | 10.0 / 0.0 (vacuous, marker) | pass |
| Prob005_notgate | one LUT | out of context | 7.905 / 0.840 | pass |
| Prob015_vector1 | wiring only | chip_top | 3.646 / 1.853 | pass (I/O buffers) |
| Prob036_ringer, Prob031_dff, Prob038_count15 | regression kinds | out of context | 7.905/0.840, 7.006/1.061, 8.363/0.238 | pass, unchanged |

In the first run Vivado completed every command for vector1, printed
SYNTH_COMPLETE, then crashed while exiting; the rerun with the shutdown-crash
rule passed (the crash did not recur, so it is intermittent).

## Reference synthesis sweep (`reference_synthesis_sweep.json`, `synth_sweep.py`)

Every official reference of the 40 registered final tasks, out of context,
without the harness's severity promotions: 39 of 40 synthesize and pass the
gate, including five zero-cell designs (vector0, vector1, vector4, wire4,
m2014_q4i). Prob137_fsm_serial's reference infers latches (`Synth 8-327`), which
leaves its paths untimed; the harness promotes that message to an error, so a
harness-built design cannot take that shape. The sweep qualifies the tool flow
on known-good designs; it uses no model output and does not change the task set.

Taxonomy: empty_netlist_unplaceable, vivado_exit_crash_after_completion.
