# PLAN — iteration 2

## Current state assessment

Iteration 1 is the verified timing-recovery incumbent at 23 LUTs and 15 FFs, with routed WNS 0.105 ns and WHS 0.050 ns. The current seed already uses a registered `head` to keep the FIFO output off the dynamically indexed memory path. Since timing is now feasible, iteration 2 must strictly reduce LUTs (or tie LUTs and reduce FFs) to improve the `minimize_luts` objective.

## Hypothesis

Keeping the oldest word only in `head` and storing only the remaining words in the tail queue can reduce distributed-memory storage and its selection logic, while preserving the registered output path.

## Instruction for generator

In `sync_fifo_core`, change the full-depth `memory` ring so it stores only queued words behind `head`; write the tail on pushes into a nonempty FIFO, and load the next head from the tail on pops when more than one word is queued. Handle `DEPTH=1` explicitly, including simultaneous pop and push, and preserve arbitrary-depth wrap, full simultaneous transfers, stalls, reset behavior, and the one-cycle minimum transfer age. Keep the top interface and `// @latency 1` annotation; retain `sync_fifo_core` as a live child, then compare routed LUTs, FFs, WNS, and WHS against the incumbent.