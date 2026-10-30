# PLAN — iteration 1

## Current state assessment

The incumbent uses 55 LUTs and 37 FFs, with routed setup WNS 0.494 ns and hold WHS 0.113 ns, so timing is feasible. The objective is strictly fewer LUTs while retaining timing feasibility and passing every verification gate. The top’s numeric latency is unknown; preserve its observable cycle behavior without adding a latency annotation.

## Hypothesis

Replacing the explicit all-ones wrap comparison and count-selection branch with natural WIDTH-bit increment wrap should remove redundant selection logic and reduce LUT use.

## Instruction for generator

In the sequential count/overflow logic, replace the `count_next` temporary and the `count == {WIDTH{1'b1}}` branch with a direct `count <= count + 1'b1` on enabled increments; update overflow to assert exactly when the pre-edge count is all ones, clear on load and enabled non-wrap increments, and hold while disabled. Preserve synchronous reset priority, load-over-enable priority, registered threshold flags based on the pre-edge count, all parameter behavior, and every output’s cycle behavior. Do not add a numeric latency annotation; the current top latency is unknown.