# PLAN — iteration 3
## Current state assessment
Iterations 1 and 2 are accepted improvements, and the verified incumbent is timing-feasible at 30 LUTs and 45 FFs. The seed already combines the dividend shift with `quotient_work` and uses a width-sized iteration counter, so those changes should not be repeated. The divider’s separate `quotient_reg` and `remainder_reg` duplicate the final values already held in the work registers; the top must retain `// @latency 9`.

## Hypothesis
Drive the registered outputs from the work registers and remove the duplicate result registers to reduce FF and output-selection logic while preserving the valid result and its stall behavior.

## Instruction for generator
In `iterative_divider_core`, connect `quotient` and `remainder` directly to `quotient_work` and `remainder_work`, then remove `quotient_reg` and `remainder_reg` and their reset and final-iteration assignments. Keep the work registers reset and update them on the same compute edges, so the final tuple becomes visible with `out_valid` and remains stable while a result is held. Preserve the top interface, `// @latency 9`, handshake, reset priority, and WIDTH-dependent schedule; invalid output payload is unspecified by the contract.