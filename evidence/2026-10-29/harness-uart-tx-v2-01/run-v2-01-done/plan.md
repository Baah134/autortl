# PLAN — iteration 3
## Current state assessment
Iteration 1 is the verified best at 26 LUTs and passed simulation, tool, and routed timing gates. Iteration 2 passed those gates but used 28 LUTs, so it did not improve the timing-feasible incumbent. The current seed keeps `busy` and `in_ready_reg` as separate state even though their values are complementary across reset, acceptance, transmission, and completion.

## Hypothesis
Drive registered `in_ready` as `~busy` and remove the redundant ready register to reduce state and possibly LUT use while preserving edge-aligned output behavior.

## Instruction for generator
In `uart_tx`, replace `in_ready_reg` with a continuous `assign in_ready = ~busy`, remove its sequential assignments, and use the existing `busy` state for acceptance and completion control. Keep the indexed `data_reg[bit_index]` serializer; iteration 2’s shift-based serialization did not improve LUT use. Preserve the counter schedule, reset priority, registered `tx`, exact frame timing, and `// @latency 1`; promotion still requires all fixed simulation, tool, metric-integrity, and setup/hold gates plus strictly fewer than 26 routed LUTs.