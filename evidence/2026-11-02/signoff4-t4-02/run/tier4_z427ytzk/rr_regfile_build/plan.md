# PLAN — iteration 2
## Current state assessment
The incumbent is timing-feasible at 42 LUTs and 90 FFs, so this iteration must strictly reduce LUTs (or match 42 LUTs with fewer than 90 FFs) to improve the objective. Iteration 1 passed behavior and timing but removing `wr_en_reg` did not improve the objective; the top’s numeric latency is unknown, so no numeric top annotation is required.

## Hypothesis
Replacing the arbiter’s encoded winner, shift-generated grant, and case-selected payload with a one-hot winner mask and masked-OR payload selection may reduce LUT use while retaining the registered outputs.

## Instruction for generator
In `rr_arbiter4`, derive a one-hot winner mask from `last` and `req`, preserving the specified cyclic priority, then register that mask directly as `grant_reg`. Use the mask to select `wr_addr_reg` and `wr_data_reg` with masked-OR logic instead of encoding `winner` and using the `case` payload mux; retain the existing `last`, reset, idle, and registered output behavior. Do not repeat the iteration 1 change that removes `wr_en_reg`; preserve the top interface and exact cycle behavior.