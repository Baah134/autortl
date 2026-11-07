# PLAN — iteration 2
## Current state assessment
Iteration 1 is the verified timing-feasible incumbent: 12 LUTs, 18 FFs, WNS 0.122 ns, and WHS 0.104 ns. Since timing is closed, iteration 2 must strictly reduce LUTs, or keep LUTs at 12 and reduce FFs, while passing the same behavioral and routed-report gates. The incumbent’s front/back registers removed the pointer-selected output path that failed setup in the baseline.

## Hypothesis
Replacing the binary occupancy counter and its increment/decrement decode with two queue-valid state bits may reduce LUT use while retaining the incumbent’s registered output path and timing feasibility.

## Instruction for generator
In `skid_buffer_core`, replace `occupancy` with two valid bits for the front and back entries, using only legal states for empty, one-word, and full; derive `out_valid` from front-valid and `in_ready` from back-valid plus `out_ready`. Update those bits for push-only, pop-only, simultaneous push/pop, and reset while preserving the existing front/back data movement, full-width payloads, stall stability, and one-word-per-cycle throughput. Keep data registers unreset if they are unreset in the incumbent, retain the top’s `// @latency 1`, and preserve all ports and cycle behavior.