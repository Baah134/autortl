# PLAN — iteration 3

## Current state assessment

Iteration 2 is the verified best at 16 LUTs and 18 FFs, with timing met (WNS 0.445 ns, WHS 0.011 ns). Since both it and the candidate must be timing-feasible, promotion requires fewer LUTs, or equal LUTs and fewer FFs. Iteration 1’s explicit CRC equations left LUT and FF counts unchanged, so repeating that change alone is unlikely to improve the objective.

## Hypothesis

Move the frame-start selection through the CRC’s linear transform and fold it into per-bit Boolean equations, which may reduce LUT use by replacing the 16-bit `crc_state` mux with output-side constant selection.

## Instruction for generator

In `crc16_stream_core`, replace `crc_state = out_last_reg ? 16'hFFFF : out_crc_reg` followed by `crc16_update(crc_state, in_data)` with Boolean equations that compute the byte-data contribution and select between the transformed `out_crc_reg` and the fixed transformed frame-start value (`T(16'hFFFF) = 16'hE1F0`). Fold `out_last_reg` into those output equations rather than building a separate 16-bit state mux; preserve the CRC result for every accepted byte and the existing one-slot handshake, reset, registered-output, and cycle behavior. Keep the top `// @latency 1` annotation, and evaluate promotion only with the unchanged integration testbench and all routed timing, utilization, and metric-integrity gates.