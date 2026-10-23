# EVALUATION — iteration 1
## Contract check
- Interface and parameters: PASS — top name, ports, widths, directions, parameter names, and defaults are preserved.
- Reset and cycle behavior: PASS — synchronous reset priority, load/enable behavior, overflow hold and clear behavior, registered flags, and count update semantics are preserved.
- Top latency annotation: PASS — authoritative `declared_latency.known=false`; no numeric annotation is required.
- Deterministic ladder: PASS — standard ladder reports 5 rungs ALIVE.
- Compile, elaborate, and simulate: PASS — required tool exits are zero; simulation reports the exact `TEST PASSED` verdict.
- Synthesis and metric integrity: PASS — synthesis succeeded with `SYNTH_COMPLETE`; retained routed reports and hashes are present.
- Timing feasibility: PASS — `timing_met=true`, WNS is 0.126 ns, and WHS is 0.026 ns.
- LUT objective and improvement: PASS — LUTs decreased from 55 to 31 while both candidate and previous best are timing-feasible; recorded improvement kind is `objective`.
## Summary
- Passed: 8 of 8
- Failed: 0 of 8
- Improved over previous best: YES
## Recommendation
ACCEPT
## Reason
The candidate preserves the counter’s defined interface and observable behavior, passes the deterministic verification and tool gates, and has nonnegative routed setup and hold slack. With the previous best also timing-feasible, the strict LUT objective is met: usage fell from 55 to 31.