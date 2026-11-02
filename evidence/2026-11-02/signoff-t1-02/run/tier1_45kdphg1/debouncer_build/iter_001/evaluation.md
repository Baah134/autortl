# EVALUATION — iteration 1
## Contract check
- Top interface and latency annotation: PASS — ports match the contract and `// @latency 0` matches authoritative top latency.
- Defined behavior: PASS — the standard ladder is ALIVE and simulation passes; the candidate preserves the 8-cycle debounce behavior and synchronous reset.
- Compile, elaboration, and simulation: PASS — xvlog, xelab, and xsim exited successfully; the exact `TEST PASSED` verdict is present.
- Synthesis and process receipts: PASS — Vivado exited successfully, `SYNTH_COMPLETE` is present, and required tool exits are recorded as successful.
- Routed metric integrity: PASS — retained routed reports are identified by hashes and provide the reported metrics.
- Timing closure: PASS — timing is met with WNS 0.731 ns and WHS 0.183 ns.
- Objective improvement: PASS — LUTs decreased from 6 to 4 and FFs from 6 to 5, improving the `minimize_luts` objective.
## Summary
- Passed: 7 of 7
- Failed: 0 of 7
- Improved over previous best: YES
## Recommendation
ACCEPT
## Reason
The candidate passes deterministic behavioral and tool gates, meets setup and hold timing requirements, and improves the chosen objective with fewer LUTs and FFs than the previous best.