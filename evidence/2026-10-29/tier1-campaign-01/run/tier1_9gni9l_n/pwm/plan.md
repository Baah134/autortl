# PLAN — iteration 5
## Current state assessment
The verified incumbent is already timing-feasible at 7 LUTs, with WNS 0.553 ns and WHS 0.135 ns, so iteration 5 must use fewer LUTs to improve the minimize_luts objective. The prior trials rejected narrower counters, alternative wrap handling, a comparator rewrite, and reverse counting; the watchdog reports three consecutive iterations without improvement. The current top’s numeric latency is unknown, so no numeric annotation is required.

## Hypothesis
Splitting the modulo-256 increment into two 4-bit sections may map the counter carry logic more compactly while retaining the existing comparator and output register.

## Instruction for generator
Replace the counter increment pattern with a low-nibble increment each non-reset cycle and a high-nibble increment only when the old low nibble is `4'hf`; reset both nibbles to zero so the count wraps naturally from 255 to 0. Keep `pwm_out <= (counter < {24'd0, duty})` and the synchronous reset behavior unchanged. Preserve the exact output sequence and duty sampling cycle, including counter wrap and changing duty values, and require fewer than 7 routed LUTs plus all fixed verification and timing gates for promotion.