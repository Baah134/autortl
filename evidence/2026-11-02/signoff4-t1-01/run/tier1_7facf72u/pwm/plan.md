# PLAN — iteration 5
## Current state assessment
The timing-feasible incumbent uses 7 LUTs and 9 FFs, so this iteration must strictly reduce LUTs to improve the objective. Earlier counter-width, comparator, and sliced-increment proposals were rejected or increased LUT use; the frozen source and testbench pass, and top numeric latency is unknown, so no annotation is required.

## Hypothesis
Explicitly sharing the counter’s upper-bit-zero reduction between the terminal-count check and PWM comparison may reduce LUT use while preserving the full-width behavior.

## Instruction for generator
Keep the 32-bit counter, reset, registered output, and cycle behavior unchanged. Define a shared reduction for `counter[31:8] == 0` and use it with `&counter[7:0]` for the terminal-count check and with `counter[7:0] < duty` for the output comparison, preserving equivalence to the full 32-bit unsigned comparison. Measure routed LUTs against the 7-LUT incumbent and retain the candidate only if every deterministic gate passes and LUT count is strictly lower.