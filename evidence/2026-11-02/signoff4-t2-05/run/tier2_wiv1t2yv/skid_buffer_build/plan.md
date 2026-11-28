# PLAN — iteration 2

## Current state assessment
Iteration 1 is the verified best: it passed simulation and all promotion gates, reduced LUTs from 15 to 14, and retained 19 FFs. Routed setup and hold slack are both positive but narrow at 0.088 ns and 0.158 ns; the objective remains `minimize_luts`.

## Hypothesis
Replacing the binary occupancy register plus redundant registered `out_valid` with `valid` and `full` state flags may reduce occupancy decode logic and FF usage while preserving the same FIFO behavior.

## Instruction for generator
In `skid_buffer_core`, replace `occupancy` and `occupancy_next` with `valid` and `full` registers; drive `out_valid` from `valid` and `in_ready` from `!full || out_ready`. Update the flags from the existing `push` and `pop` handshakes: `valid` tracks whether the queue is nonempty, and `full` sets when a push without a pop fills the second slot and clears on a pop without a push. Translate the data-register update conditions to use `valid` and `full`, preserving FIFO ordering, simultaneous transfers, stall stability, synchronous reset behavior, and the top’s `// @latency 1` annotation.