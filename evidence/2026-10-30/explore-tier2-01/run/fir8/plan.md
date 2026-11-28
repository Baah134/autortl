# PLAN — iteration 4
## Current state assessment
The three candidates passed the reported behavioral and build checks but were rejected for setup timing; the best reported WNS is still −3.797 ns, with hold slack +0.100 ns. The routed trial shows two DSP48E1 stages followed by carry logic on the critical path. The symmetric-folding trial therefore improved WNS over the baseline but did not close timing. The top’s known latency is 1 cycle, so retain `// @latency 1`.

## Hypothesis
For the default symmetric coefficients, replacing DSP-mapped constant multiplications with widened shift-add arithmetic should remove the observed DSP cascade and improve setup slack, at the cost of more LUTs and carry logic.

## Instruction for generator
Keep the delay registers, reset logic, sequential assignments, ports, parameters, and latency annotation unchanged. In a compile-time branch for the exact default coefficient values, pair `d[0]+d[7]` through `d[3]+d[4]`, then implement multiplication by 3, 7, 12, and 18 using signed shift-add expressions widened before shifting; combine the four results with a balanced 32-bit sum tree into the existing `sum_pipe0` assignment. Preserve the original arithmetic as the fallback for every other parameter combination, and preserve the existing 32-bit result semantics. Promote only if the fixed verification and evidence gates pass, setup and hold slack are both nonnegative, and the candidate satisfies the objective policy.