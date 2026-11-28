# PLAN — iteration 6
## Current state assessment

Iteration 4 is the verified timing-feasible incumbent at WNS 0.807 ns. Iteration 5 and the advisor trial are timing-infeasible at WNS −0.341 ns; the trial’s reported critical path reaches `y_out` through a 9-level path. The current seed has registered products feeding a carry-save reduction and a final 32-bit adder, so preserve those registers and focus on the final adder.

## Hypothesis

Replacing the final 32-bit carry-propagate addition with a segmented carry-select adder may shorten the product-register-to-output path enough to close timing and improve register-to-register slack over the incumbent.

## Instruction for generator

Keep `p0`–`p7`, the carry-save reduction, `y_out`, reset behavior, parameters, and `// @latency 1` unchanged. Replace only `sum_all = s6 + c6` with a 32-bit segmented carry-select sum: compute a low chunk’s sum and carry, compute each upper chunk’s sums for carry-in 0 and 1, then select by the preceding chunk’s carry. Preserve exact modulo-32-bit addition semantics; evaluate the routed timing, especially `reg2reg_wns_ns`, against the 0.807 ns incumbent and retain the candidate only if all gates pass and the objective improves.