# PLAN — iteration 2
## Current state assessment
Iteration 1 is the verified best: it passes simulation and routed setup/hold timing, with 11 LUTs and 18 FFs. Since timing is already feasible, iteration 2 must strictly reduce LUTs (or keep LUTs equal and reduce FFs) to improve the `minimize_luts` objective. The current head-valid/tail-valid design is the seed; no failed trial is reported.

## Hypothesis
Writing the two validity flags from direct Boolean next-state equations and using shared, explicit head/tail write enables may reduce control LUTs while preserving the FIFO’s cycle behavior.

## Instruction for generator
In `skid_buffer_core`, replace the nested occupancy branches that update `head_valid` and `tail_valid` with direct next-state equations derived from `push`, `pop`, and the current validity flags. Replace the branch-specific data-register conditions with explicit shared write enables: shift `data1` into `data0` when a full queue pops, write `in_data` into `data0` when an accepted input becomes the head, and write `in_data` into `data1` when the tail is filled or replaced. Preserve synchronous reset priority, combinational `in_ready`, no empty fallthrough, stalled output stability, and simultaneous full pop/push behavior; retain `// @latency 1` on the top. Compare routed LUTs and FFs against the 11-LUT, 18-FF incumbent, and keep the candidate only if all gates pass and the objective improves.