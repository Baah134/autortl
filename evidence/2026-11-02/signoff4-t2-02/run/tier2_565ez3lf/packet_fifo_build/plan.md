# PLAN — iteration 3

## Current state assessment

Iteration 2 is the verified best: it closed timing with WNS 0.043 ns and WHS 0.101 ns, at 28 LUTs and 42 FFs. The objective is now strictly fewer LUTs while preserving timing closure; iteration 1’s direct indexed-output FIFO was rejected, and iteration 2’s registered head fixed its RAM-to-output timing path.

## Hypothesis

Keeping the registered head while storing only the remaining `DEPTH-1` tuples in the circular tail buffer should reduce distributed-RAM LUT use while retaining the registered output path.

## Instruction for generator

In `packet_fifo_core`, replace the full-depth `data_mem`/`last_mem` plus duplicated head storage with a registered head tuple and a circular tail buffer of capacity `DEPTH-1`; use a dedicated `DEPTH==1` case so all supported configurations elaborate correctly. On an empty push, load the head; on a pop with more than one queued tuple, load the old tail head and advance its read pointer; write accepted tuples behind the head, including full simultaneous pop/push. Preserve explicit pointer wrap, occupancy, synchronous reset priority, the ready equation, minimum transfer age, stall stability, all payload bits, and the top’s `// @latency 1`; evaluate LUT reduction only if simulation, routed setup, and hold gates all pass.