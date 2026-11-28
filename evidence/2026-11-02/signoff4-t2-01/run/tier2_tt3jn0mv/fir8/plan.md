# PLAN — iteration 6
## Current state assessment
Iteration 5 is the verified timing-feasible best, with routed WNS 1.431 ns, positive hold slack, and a matching `// @latency 1` annotation. Because the objective is `maximize_freq`, iteration 6 must pass every deterministic and routed evidence gate and strictly improve the incumbent’s register-to-register setup slack at the same clock period. The OOC flow times internal clocked paths; its missing I/O delays are advisory context.

## Hypothesis
Fusing each default shift/add coefficient calculation with its corresponding `pN + sN` accumulation through carry-save compression may shorten the register-to-register logic depth and improve routed setup slack, at the cost of some LUTs.

## Instruction for generator
Keep `// @latency 1`, the delay and partial-sum registers, `y_out`, and all reset and update behavior unchanged. For each default-coefficient branch, replace the serial shift/add product followed by `pN + sN` with a 32-bit carry-save combination of the shifted `x_d` terms and the matching partial sum, followed by one carry-propagate addition; preserve modulo-32-bit signed results, including the subtraction case for coefficient 7. Keep the generic parameter fallback arithmetic unchanged, and validate every supported independent coefficient override. Retain the candidate only if simulation and all evidence gates pass, routed WNS and WHS are nonnegative, and register-to-register setup slack strictly exceeds 1.431 ns.