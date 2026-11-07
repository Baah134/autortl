# EVALUATION — iteration 1
## Contract check
- Defined behavior and interface: PASS — the candidate preserves the 8-sample debounce sequence, synchronous active-high reset behavior, ports, and registered output; the authoritative ladder is ALIVE.
- Top latency annotation: PASS — `// @latency 0` matches the authoritative known latency.
- Compile, elaboration, and simulation: PASS — required tool exits are zero; simulation reports `TEST PASSED`.
- Routed metric integrity: PASS — retained routed reports are identified, and candidate utilization and timing metrics are consistent.
- Timing closure: PASS — `timing_met=true`, WNS is 0.731 ns, and WHS is 0.067 ns.
- Objective improvement and promotion: FAIL — both candidate and previous best are timing-feasible, but LUTs and FFs are unchanged; no strict `minimize_luts` improvement is established.
## Summary
- Passed: 5 of 6
- Failed: 1 of 6
- Improved over previous best: NO
## Recommendation
REJECT
## Reason
The candidate passes behavioral, verification, metric, and timing gates, but it does not improve the chosen objective over the already timing-feasible previous best. Equal LUT and FF counts do not satisfy the required strict objective improvement.