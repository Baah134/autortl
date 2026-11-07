# PLAN — iteration 5
## Current state assessment
The incumbent is already timing-feasible at 7 LUTs and 9 FFs, and the objective requires a strict LUT or FF improvement. Prior attempts using an 8-bit modulo counter and rewritten duty comparisons were rejected; the current top’s numeric latency is unknown, so no numeric annotation is required.

## Hypothesis
Writing the counter’s modulo-256 update as per-bit toggle equations may let Vivado map its carry conditions more compactly, but the LUT count must be checked against the 7-LUT incumbent.

## Instruction for generator
Replace only the counter increment and wrap logic with explicit next-bit equations: bit 0 toggles every cycle, and bit *i* toggles when all lower counter bits are one. Keep the counter at 8 bits, preserve synchronous reset and the registered `pwm_out <= (counter < {24'd0, duty})` behavior exactly. Do not add a latency annotation; promote only if all gates pass and LUTs decrease, or LUTs remain equal with fewer FFs.