# PLAN — iteration 3
## Current state assessment
Iteration 2 is the verified, timing-feasible incumbent at 27 LUTs and 17 FFs, with WNS 0.329 ns and WHS 0.197 ns. Since timing is closed, promotion now requires a strict improvement in `(LUTs, FFs)`; timing recovery or progress alone does not qualify.

## Hypothesis
Deriving `out_valid` from the existing occupancy register instead of storing `out_valid_reg` should remove one FF and its update logic, with a chance to reduce LUTs while preserving timing closure.

## Instruction for generator
In `packet_fifo_core`, remove `out_valid_reg` and its reset and case updates, and drive `out_valid` as `(occupancy != 0)` from the existing occupancy state. Keep the `has_space` register and all FIFO storage, head-update, pointer-wrap, and occupancy behavior unchanged; preserve the top’s `// @latency 1` annotation and all defined handshakes, stalls, reset behavior, and minimum transfer age. Check the full parameter matrix and retain the candidate only if all gates pass and routed timing remains feasible; promotion requires fewer LUTs, or equal LUTs with fewer FFs than the incumbent.