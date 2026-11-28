# PLAN — iteration 3
## Current state assessment
Iteration 2 is the timing-feasible incumbent at 16 LUTs and 18 FFs, with WNS 0.445 ns and WHS 0.011 ns. It improved on iteration 1 by reusing `out_crc_reg` as the frame state; iteration 1’s explicit factored GF(2) equations did not improve the objective. Since the objective is `minimize_luts`, the next candidate must reduce LUTs while preserving the known top latency of 1 and all stream behavior.

## Hypothesis
Replacing the 16-bit frame-seed mux before the CRC update with an equivalent linear CRC transform and conditional constant correction may reduce LUT usage while retaining the 18 required FFs and single-cycle update.

## Instruction for generator
In `crc16_stream_core`, change the `crc_seed` / `crc_next` logic so the CRC update is expressed using CRC linearity: separate the data contribution and the `out_crc_reg` state contribution, then apply the fixed `0xFFFF` state correction when `out_last_reg` is set. Keep the existing registered outputs, handshake, reset priority, and `// @latency 1`; preserve the CRC result for consecutive frames and stalled transfers. This is a distinct transformation from iteration 1’s explicit factored equations: evaluate whether removing the full-width seed mux lowers routed LUT count, and retain the candidate only if all verification and metric gates pass with strict LUT improvement over the 16-LUT incumbent.