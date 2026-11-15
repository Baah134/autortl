# Out-of-context port timing for designs with no internal path — November 14, 2026

Live Vivado 2025.2, xc7a35tcpg236-1, 10 ns, `autortl.vivado.run_synthesis` with
`implementation=out_of_context`, VerilogEval c498220 references renamed
TopModule (`ooc_timing_live.json`).

| Design | Kind | WNS / WHS (ns) | Gate |
|---|---|---|---|
| Prob036_ringer | combinational (virtual clock) | 7.905 / 0.840 | pass |
| Prob038_count15 | register-to-register paths (ports stay untimed) | 8.363 / 0.238 | pass, identical to pilot-04 arm C |
| Prob031_dff, ports timed, input hold checked | single register | 7.006 / -0.833 | pass, but timing_met false (artificial hold) |
| Prob031_dff, final template | single register | 7.006 / 1.061 | pass, timing met |

With the input-hold false path in place and `report_qor_suggestions` still
enabled, Vivado crashed twice in that report (`Abnormal program termination
(EXCEPTION_ACCESS_VIOLATION)`) after all metrics reports were written; triage
then classified the crash as DESIGN. The final template skips that advisory
report when the port guard fires, and triage now classifies the crash banner as
INFRA. Taxonomy: single_register_design_untimed_ooc,
vivado_crash_classified_design. Before this change pilot-04's Prob147_circuit10
arm C baseline (a single register stage) was blocked by the metrics gate.
