# PLAN — iteration 6

## Current state assessment

The verified incumbent is timing-feasible with WNS and register-to-register WNS of 0.329 ns and WHS of 0.076 ns. Iterations 3 and 4 tried carry-select changes to the final adder without improving the objective, and iteration 5 tried a transposed FIR that also failed to improve it. The candidate must pass every verification and routed-metric gate, preserve the known one-cycle behavior and `// @latency 1`, and strictly exceed 0.329 ns register-to-register WNS to replace the incumbent.

## Hypothesis

Rebalancing the existing carry-save reduction into parallel Wallace-style compressor layers may shorten the longest product-register-to-output path and improve register-to-register setup slack.

## Instruction for generator

Keep the product delay chains, coefficient multipliers, reset logic, output register, interface, and `// @latency 1` unchanged. Change only the grouping and wiring of the current `a0`–`a7` 3:2 carry-save reduction so each layer compresses available operands in parallel and the final two vectors feed the existing 32-bit carry-propagate addition. Preserve exact modulo-32-bit sum behavior for every supported parameter value; retain the candidate only if all deterministic and routed-report gates pass and register-to-register WNS strictly exceeds 0.329 ns.