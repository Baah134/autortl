# PLAN — iteration 1
## Current state assessment
The default 32-bit counter meets the 10 ns timing target with WNS 0.494 ns and WHS 0.113 ns, using 55 LUTs and 37 FFs. Since the incumbent is already timing-feasible, promotion requires a strictly lower LUT count. The seed has a dead `prev_count` register and temporary `count_next`; synthesis may already remove the dead register, so the LUT benefit is uncertain. Top-level numeric latency is unknown; preserve the existing cycle behavior without adding an annotation.

## Hypothesis
Removing the dead register and expressing increment-and-wrap as a single width-limited addition may reduce redundant next-state logic and LUT usage while retaining timing feasibility.

## Instruction for generator
Remove `prev_count` and its assignments, since it is never read. Replace the blocking `count_next` temporary and full-width all-ones comparison with a width-limited increment whose natural modulo wrap sets `overflow` on the enabled wrap cycle; preserve synchronous reset priority, load-over-enable priority, disabled count hold, and overflow hold while disabled. Keep all registered threshold flags evaluating the pre-edge `count`, including their reset values and updates during disabled and load cycles. Do not change ports, parameters, or observable cycles.