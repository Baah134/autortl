# PLAN — iteration 3
## Current state assessment
Iteration 1 is the verified best at 33 LUTs, 46 FFs, WNS 0.313 ns and WHS 0.095 ns; it passed the fixed behavioral and tool gates. Iteration 2 repeated the compare/subtract proposal and was rejected because it did not reduce LUTs, and the watchdog reports identical-code churn. Both the best and baseline are timing-feasible, so promotion requires strictly fewer than 33 LUTs while preserving the known top annotation `// @latency 9` and all defined behavior.

## Hypothesis
A non-restoring remainder recurrence may reduce LUT use by replacing the per-cycle compare, conditional subtract and remainder selection with one add/subtract datapath, while keeping the existing iteration count and registers.

## Instruction for generator
In `iterative_divider_core`, replace the restoring `trial_remainder >= divisor_reg` plus conditional-subtraction pattern with a non-restoring recurrence: subtract the divisor when the prior partial remainder is nonnegative, otherwise add it, and derive each quotient bit from the updated remainder’s sign. Use the existing `remainder_work` and `quotient_work` state, and correct a negative final partial remainder before registering the output. Preserve zero-divisor results, all supported widths including `WIDTH=1`, the exact cycle and handshake behavior, reset priority, registered outputs, and the required `// @latency 9` annotation; promotion still requires all gates and fewer than 33 routed LUTs.