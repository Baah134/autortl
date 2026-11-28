# PLAN — iteration 3
## Current state assessment
Iteration 2 is the timing-feasible incumbent at 29 LUTs and 16 FFs, with routed WNS 0.089 ns and WHS 0.064 ns. The output head registers and registered `full` flag are already in the seed, so this iteration targets the fixed-width counter and pointer state for the `minimize_luts` objective while preserving the closed timing gates.

## Hypothesis
Sizing the occupancy counter and ring pointers to each supported `DEPTH` will reduce unnecessary state and arithmetic logic, with the default depth-3 configuration using a 2-bit occupancy counter and 2-bit pointers.

## Instruction for generator
In `packet_fifo_core`, replace the fixed `reg [3:0] occupancy` declaration with a counter sized to represent 0 through `DEPTH`, and replace both fixed 3-bit pointer declarations with pointers sized for `TAIL_DEPTH` entries, using at least one bit for depth-1 cases. Keep explicit pointer wrap at `TAIL_DEPTH-1` and preserve the existing head/tail data movement, registered `full` update, handshakes, synchronous reset, and top `// @latency 1` annotation. Check depths 1 through 8, including full simultaneous pop/push and non-power-of-two wraps; retain the candidate only if all gates pass and routed LUT count strictly improves over the feasible incumbent.