# EVALUATION — iteration 1
## Contract check
- Behavioral and parameter semantics: PASS — The candidate preserves reset priority, load and enable behavior, overflow hold and wrap behavior, flag timing, and parameterized widths; the authoritative ladder reports ALIVE.
- Ports and declared latency: PASS — Port names, directions, widths, parameters, and defaults match the frozen source; the candidate declares `// @latency 0`.
- Frozen testbench simulation: PASS — The retained log shows the exact `TEST PASSED` verdict; candidate metrics report simulation passed.
- Synthesis completion: PASS — `SYNTH_COMPLETE` is present and `synth_error` is empty.
- Routed metrics and objective: PASS — Retained routed reports are listed; LUTs improve from 55 to 53, with WNS 0.456 ns and WHS 0.282 ns, both nonnegative.
- Required tool exit codes: INVESTIGATE — The evidence previews show successful stage output, but do not establish successful exit codes for every required tool stage.
## Summary
- Passed: 5 of 6
- Failed: 0 of 6
- Improved over previous best: YES
## Recommendation
REJECT
## Reason
The candidate shows a measured LUT improvement and passes the reported behavioral, simulation, synthesis, and routed timing gates. However, the evidence does not establish successful exit codes for every required tool stage, and unknown mandatory evidence cannot count as success.