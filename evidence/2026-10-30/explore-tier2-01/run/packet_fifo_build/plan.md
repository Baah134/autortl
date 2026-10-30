# PLAN — iteration 3

## Current state assessment

Iteration 2 is the verified best at 23 LUTs, WNS 0.069 ns, and WHS 0.079 ns, with all reported gates passing. The supplied seed’s metrics are unverified, so iteration 3 must establish its own routed results and remain timing-feasible before claiming a LUT improvement. The current seed keeps the required child instance and declares `// @latency 1`.

## Hypothesis

Deriving the tail write address from the read pointer and occupancy may remove one pointer register and reduce LUT use below the 23-LUT incumbent while preserving timing feasibility.

## Instruction for generator

In the top-level FIFO control, replace the registered `tail_write_ptr` and its reset, toggle, and write-address uses with a combinational address derived as `tail_read_ptr ^ (occupancy == 2'd2)`. Preserve the existing head/tail data updates, occupancy transitions, synchronous reset behavior, direct ready/valid behavior, and minimum transfer age; this address relation must hold for every reachable occupancy and simultaneous push/pop case. Keep the `packet_fifo_core` instance and its connections unchanged, and retain `// @latency 1`. This is a LUT objective experiment: promote only if all fixed gates pass, routed WNS and WHS are nonnegative, and LUT use is strictly below 23.