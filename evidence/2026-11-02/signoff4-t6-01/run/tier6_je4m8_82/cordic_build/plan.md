# PLAN — iteration 3
## Current state assessment
Iteration 2 is the verified timing-feasible incumbent at 194 LUTs, 95 FFs, and routed WNS 0.076 ns. The objective is now strictly fewer LUTs, or equal LUTs with fewer FFs, while preserving setup and hold closure and every defined cycle behavior; the top’s numeric latency is unknown, so no numeric top annotation is required.

## Hypothesis
Expressing each direction-controlled CORDIC add/subtract as one conditional-invert adder may reduce LUT use while retaining the same modulo-18-bit results and timing feasibility.

## Instruction for generator
In `cordic_engine`, replace the `x_next` and `y_next` ternary add/subtract expressions with conditional operand inversion and carry-in: for x, subtract `y_shift` when `z_state[19]` is clear and add it otherwise; for y, add `x_shift` when clear and subtract it otherwise. Keep the 18-bit arithmetic result, arithmetic shifts, z update, registers, handshakes, reset behavior, and output updates unchanged. Preserve the top interface and do not add a numeric top latency annotation.