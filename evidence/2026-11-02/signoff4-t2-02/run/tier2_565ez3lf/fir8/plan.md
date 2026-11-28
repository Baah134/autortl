# PLAN — iteration 6
## Current state assessment
The incumbent is timing-feasible at WNS 0.148 ns and WHS 0.182 ns, with 133 LUTs and 112 FFs. Since the objective is `maximize_freq`, this iteration must preserve timing closure and strictly improve register-to-register setup slack over 0.148 ns; simulation, annotation, synthesis, routed-report integrity, setup, and hold gates remain mandatory. Iteration 5’s accumulator-width reduction was rejected, and a separate parallel-product trial remained timing-infeasible, so neither should be repeated unchanged.

## Hypothesis
For the exact default coefficients, pairing symmetric delay taps before coefficient multiplication and reducing the four weighted pairs with carry-save logic may shorten the critical register-to-register path while preserving the one-cycle FIR behavior.

## Instruction for generator
Add an exact-default-coefficient generate branch that forms signed 17-bit sums `d[0]+d[7]`, `d[1]+d[6]`, `d[2]+d[5]`, and `d[3]+d[4]`, then applies weights 3, 7, 12, and 18 using explicit shift-add expressions. Reduce those four signed 32-bit weighted terms with a carry-save tree and one final adder to drive the existing registered `y_out`; retain the existing generic parameter path for every other coefficient set. Keep `d[0:7]`, synchronous active-high reset behavior, `// @latency 1`, and all observable cycles unchanged, and preserve signed extension and 32-bit result semantics.