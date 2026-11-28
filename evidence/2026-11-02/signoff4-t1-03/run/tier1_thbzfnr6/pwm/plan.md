# PLAN — iteration 5
## Current state assessment
The verified incumbent is timing-feasible at 7 LUTs and 9 FFs, so this iteration must strictly reduce LUTs to improve the objective. The original 32-bit counter seed already maps to that incumbent result; prior 8-bit counter variants used 10 LUTs and were rejected. Top numeric latency is unknown, and the missing annotation is not a blocker.

## Hypothesis
A two-nibble modulo-256 counter may map its carry and increment logic into fewer LUTs than the previously tried 8-bit counter forms, while preserving the reset-reachable sequence and registered PWM output.

## Instruction for generator
Replace the 32-bit `counter` with an 8-bit counter split into low and high nibbles: increment the low nibble every non-reset cycle and increment the high nibble only when the old low nibble is `4'hF`, with natural nibble wraparound. Keep synchronous reset to zero and retain the registered `pwm_out <= (counter < duty)` behavior using the old counter value each cycle. Preserve the exact 256-cycle sequence and reset behavior; promote only if the unchanged verification gates pass and routed LUT use is strictly below 7 while timing remains feasible.