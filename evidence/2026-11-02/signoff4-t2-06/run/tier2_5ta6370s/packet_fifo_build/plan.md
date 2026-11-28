# PLAN — iteration 3

## Current state assessment
The verified incumbent is timing-feasible at 26 LUTs and 30 FFs, so this iteration must strictly reduce LUTs, or keep LUTs equal and reduce FFs, to improve the objective. Iteration 2 removed the `not_full` register but was rejected because it did not improve those counts; do not repeat that change.

## Hypothesis
Replacing variable-index tail writes with constant-slot write enables may reduce LUTs by simplifying the tail storage decode and update logic while preserving the existing state and timing behavior.

## Instruction for generator
In `packet_fifo_core`, change only the variable-index writes to `tail_data` and `tail_last` into per-slot updates using constant slot indices and occupancy-derived enables. Cover both push-only appends and simultaneous pop/push replacement, including the shift on pop, for every supported `DEPTH` from 1 through 8. Preserve the registered head, occupancy and `not_full` behavior, reset handling, handshakes, stall stability, minimum transfer age, and the top’s `// @latency 1` annotation; judge the candidate by the required simulation, routed timing, and resource gates.