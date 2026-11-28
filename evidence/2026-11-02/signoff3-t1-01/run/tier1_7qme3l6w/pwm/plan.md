# PLAN — iteration 5
## Current state assessment
The verified incumbent is timing-feasible at 7 LUTs and 9 FFs, so iteration 5 must strictly reduce LUTs, or keep LUTs equal and reduce FFs, to improve `minimize_luts`. Iterations 1–4 were rejected after counter narrowing, explicit wrap, split-nibble counting, and comparator changes failed to improve the incumbent; the supplied 32-bit counter is already measured at only 9 FFs, so narrowing alone is unlikely to help. Top numeric latency is unknown; preserve the registered PWM output and synchronous active-high reset without adding an annotation requirement.

## Hypothesis
An explicit per-bit toggle counter may map the modulo-256 increment with fewer LUTs than the arithmetic increment and wrap logic while preserving the PWM cycle behavior.

## Instruction for generator
Replace the 32-bit counter with an 8-bit modulo-256 counter whose bit 0 toggles each active cycle and whose bit `i` toggles when all lower bits are 1; reset it synchronously to zero. Keep `pwm_out` registered with the existing `counter < duty` comparison using the pre-edge counter value, and clear it on reset. Preserve the interface and all observable behavior, including reset and output timing; do not add a numeric top latency annotation. Retain the candidate only if all verification and routed metric gates pass and its LUT/FF pair strictly improves on the feasible 7-LUT, 9-FF incumbent.