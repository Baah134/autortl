# EVALUATION — iteration 1
## Contract check
- Top interface and edit boundary: PASS — `aes128_core` is present with the contracted ports; the candidate is a complete unit with no frozen companion.
- Defined behavior and cycle semantics: PASS — authoritative ladder is ALIVE, and the unchanged integration testbench reports `TEST PASSED`.
- Top latency annotation: PASS — authoritative top latency is unknown, so a missing numeric top annotation is permitted; child metadata does not set this requirement.
- Compile, elaboration, and simulation gates: PASS — xvlog, xelab, and xsim exited successfully; simulation passed.
- Routed reports and metric integrity: PASS — required routed reports are retained, and synthesis completed with the required marker.
- Timing closure: PASS — timing is met; setup WNS is 2.27 ns and hold WHS is 0.177 ns.
- Improvement over previous best: PASS — valid timing recovery from a timing-infeasible incumbent; LUTs also decreased from 9,108 to 627.

## Summary
- Passed: 7 of 7
- Failed: 0 of 7
- Improved over previous best: YES

## Recommendation
ACCEPT

## Reason
The candidate passes the deterministic behavioral and tool gates, preserves the contracted top interface and cycle behavior, and has consistent routed evidence showing nonnegative setup and hold slack. Its verified timing recovery qualifies it to replace the timing-infeasible previous best, and it also reduces LUT usage substantially.