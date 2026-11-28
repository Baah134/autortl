# PLAN — iteration 5
## Current state assessment
The timing-feasible incumbent uses 7 LUTs and 9 FFs, and the objective requires a strict LUT reduction (or, at equal LUTs, fewer FFs). Iterations 1–3 either changed the 32-bit counter’s behavior or increased resources; iteration 4 preserved behavior but matched the incumbent. The current source still has a 32-bit counter that resets at 255, so the unused upper bits are always zero after reset, but narrowing its declared width already failed to improve and must not change observable behavior.

## Hypothesis
Rewriting the 32-bit conditional wrap/increment as a 32-bit addition of one gated by `counter != 32'd255`, followed by a masked wrap-to-zero value, may let Vivado share the comparison and simplify the next-state mux enough to reduce LUTs while preserving the reset-at-255 sequence.

## Instruction for generator
Keep the 32-bit `counter`, synchronous active-high reset, and registered `pwm_out` comparison unchanged. Change only the counter next-state expression: derive a 32-bit increment enable from `counter != 32'd255`, then form the next value so the counter is zero at 255 and otherwise advances by one. Preserve the exact 32-bit wrap behavior and verify that the mapped design strictly improves LUTs (or ties LUTs with fewer FFs) against the incumbent; otherwise retain the incumbent.