# PLAN — iteration 3
## Current state assessment
Iteration 1 is the verified best at 20 LUTs and 20 FFs, with WNS 0.105 ns and WHS 0.18 ns, so timing is feasible and replacement requires a strict LUT or FF reduction. Iteration 2’s combined multiply-accumulate expression passed behavioral and timing gates but matched the incumbent’s resource counts, so repeating that expression alone has no demonstrated benefit.

## Hypothesis
Storing one full 18-bit stage-1 dot product instead of two 17-bit partial sums can reduce fabric FF use while preserving the two-slot, two-cycle transfer behavior.

## Instruction for generator
In `elastic_dot4_core`, replace `partial_sum_01` and `partial_sum_23` with a single 18-bit stage-1 result register, computed from the four unsigned products using a DSP48E1 cascade for the multiply-accumulate path. Keep the existing stage valid and ready logic, synchronous reset priority, stage-2 registered output, and `// @latency 2` on the top unchanged; stage 2 must capture the old stage-1 value only when ready. Preserve full carry width and verify that the deeper input-to-stage-1 path still meets setup and hold timing.