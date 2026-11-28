# PLAN — iteration 2
## Current state assessment
Iteration 1 is the verified timing-feasible incumbent: WNS 0.164 ns and WHS 0.128 ns, with 26 LUTs and 38 FFs. The current head-register design fixed the routed read-to-output path; because the objective is now minimizing LUTs, the next candidate must reduce LUT use while preserving timing feasibility and all FIFO behavior.

## Hypothesis
For the default depth of 3, replacing circular indexed storage with a three-entry shift FIFO may reduce LUT use by removing address decode and head-refill selection logic, while keeping the oldest payload in a register for the output path.

## Instruction for generator
Specialize `sync_fifo_core` for `DEPTH==3` to use three `WIDTH`-bit entry registers, with entry 0 driving `out_data`; shift entries on pop and place accepted data in the vacated or next free slot, including simultaneous push/pop cases. Keep the existing parameterized implementation for other depths, and preserve capacity, wrap-independent ordering, stalls, reset behavior, full-width payloads, and minimum transfer age. Retain the top interface and `// @latency 1`; evaluate whether routed LUTs decrease and both WNS and WHS remain nonnegative.