# PLAN — iteration 6

## Current state assessment

The incumbent is still timing-infeasible: routed WNS is −2.766 ns and register-to-register WNS is −1.989 ns, with 155 LUTs, 214 FFs, and 2 DSP48s. The seed already has balanced paired-product groups and the symmetric-coefficient path, so repeating those changes or the output-register replication trial is not indicated; iterations 3–5 produced no surviving candidate. The top must retain `// @latency 1`, its registered output and exact cycle, reset, and parameter behavior.

## Hypothesis

For the default symmetric coefficients, replacing the four constant products with balanced shift/add forms may reduce DSP and multiplier-path delay, improving setup slack at the cost of additional LUTs and carry logic.

## Instruction for generator

In the symmetric-coefficient generate branch, add a nested specialization for the exact default coefficient values (3, 7, 12, 18, 18, 12, 7, 3) that computes the four paired products with signed, explicitly sized shift/add expressions, keeping the two existing balanced partial-sum groups and pipeline registers. Retain the current multiply-based path for all other parameter values, and leave the general-coefficient branch unchanged. Preserve modulo-32-bit result behavior, reset assignments, output registration, and the latency annotation; judge the change by the unchanged simulation and routed timing gates.