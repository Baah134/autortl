# PLAN — iteration 10

## Current state assessment

Iteration 9 is the verified incumbent at 148 LUTs and 277 FFs, with setup WNS 0.751 ns and hold WHS 0.023 ns. Both timing margins are feasible, so this iteration must strictly reduce LUTs to improve the `minimize_luts` objective. The arithmetic has room for a distinct width reduction: every FIR coefficient is even, so the exact accumulator can be halved and the rounding offset and shift adjusted accordingly. Iteration 7’s narrower product widths alone increased LUTs, so this proposal combines width reduction with that arithmetic rescaling.

## Hypothesis

Halving the coefficients and using 25-bit product registers with a 27-bit half-scale accumulator may reduce multiplier and adder logic enough to lower LUT use while preserving the rounded, saturated output exactly.

## Instruction for generator

In `fir16_sym_core`, replace the eight full-scale coefficients with their halves (`-3, -10, -12, 9, 55, 113, 165, 195`), store each product in a signed 25-bit register, and use signed 27-bit partial and total accumulators. Change rounding from adding 1024 and shifting right by 11 to adding 512 and shifting right by 10, then keep the existing 16-bit saturation and result pipeline. Preserve accepted-sample history updates, all five elastic valid/ready slots, reset behavior, and the top’s `// @latency 5` annotation.