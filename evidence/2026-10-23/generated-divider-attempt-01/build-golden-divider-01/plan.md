# PLAN — iteration 3
## Current state assessment
Iteration 1 is the verified best at 30 LUTs, 39 FFs, WNS 0.315 ns, and WHS 0.11 ns; iteration 2 repeated the same divider replacement and was rejected because it also used 30 LUTs. The current top has known latency 9, so retain `// @latency 9` and the fixed schedule, handshakes, reset behavior, and registered outputs.

## Hypothesis
Sharing the restoring step’s subtract result for both the compare decision and remainder update may reduce routed LUT use below 30 while preserving timing feasibility.

## Instruction for generator
In the editable top’s restoring iteration, replace the separate `trial_remainder >= divisor` comparison and conditional subtraction with one extended-width subtraction whose top bit supplies the no-borrow decision; use that same result for the selected remainder and quotient bit. Keep the existing iteration count, capture and result registers, and control state unchanged. Preserve divide-by-zero behavior, all observable cycles, reset and stall behavior, and the matching latency annotation.