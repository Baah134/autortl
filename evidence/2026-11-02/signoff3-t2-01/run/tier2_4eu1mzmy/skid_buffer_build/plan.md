# PLAN — iteration 2
## Current state assessment
Iteration 1 is the verified best: it closes timing at WNS 0.133 ns and WHS 0.039 ns, with 11 LUTs and 19 FFs. Since both timing gates pass, iteration 2 must strictly reduce LUTs, or keep LUTs equal and reduce FFs, to improve the `minimize_luts` objective. The current seed already registers `out_valid`; the prior timing-recovery change should be retained.

## Hypothesis
Encoding the queue state directly as registered `nonempty` and `full` flags may reduce LUTs by removing occupancy comparisons while also eliminating the separate `out_valid_reg`.

## Instruction for generator
In `skid_buffer_core`, replace the binary `occupancy` counter and separate `out_valid_reg` with two state registers: `nonempty` drives `out_valid`, and `full` directly represents two queued entries for the `in_ready` rule. Update those flags for push-only and pop-only transfers, holding them on simultaneous push/pop and idle; preserve the existing data movement, synchronous reset, handshake behavior, and minimum one-cycle transfer age. Keep the top interface and `// @latency 1` annotation, and judge the candidate against the incumbent using routed reports and all existing verification gates.