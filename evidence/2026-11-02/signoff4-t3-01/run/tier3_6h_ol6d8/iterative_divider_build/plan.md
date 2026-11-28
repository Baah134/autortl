# PLAN — iteration 3
## Current state assessment
Iteration 1 is the verified best at 30 LUTs and 40 FFs with timing closure. Iteration 2’s narrower counter was rejected: it used 38 LUTs and 45 FFs, so avoid repeating that change. The current seed already removes separate result registers; its restoring step still expresses a magnitude comparison and a conditional subtraction separately.

## Hypothesis
Deriving the subtract decision and difference from one widened subtraction may reduce LUT use while preserving the one-step-per-edge schedule, though synthesis may already share some of that logic.

## Instruction for generator
In `iterative_divider_core`, replace the separate `trial_remainder >= divisor_extended` comparison and `trial_remainder - divisor_extended` expression with one explicitly widened unsigned subtraction whose top bit indicates borrow; select the difference’s low `WIDTH+1` bits when there is no borrow, otherwise retain `trial_remainder`. Keep `quotient_step`, the iteration schedule, state and handshake behavior unchanged, including the existing fixed-width counter. Preserve the top’s `// @latency 9` annotation and verify the full parameter range and all existing gates; treat any LUT reduction as a hypothesis until routed reports confirm it.