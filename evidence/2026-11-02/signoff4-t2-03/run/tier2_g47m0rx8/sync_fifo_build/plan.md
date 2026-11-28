# PLAN — iteration 2

## Current state assessment

Iteration 1 is the verified best at 13 LUTs and 6 FFs, with setup WNS −0.931 ns; timing remains infeasible. The advisor’s registered-output trial improved WNS to −0.101 ns with WHS 0.097 ns and passed simulation, but added resources and still missed setup. Its new limiting path was the occupancy-to-`in_ready` path, so repeating that trial unchanged would not address the remaining bottleneck.

## Hypothesis

Combine the registered `out_data` approach with one-hot occupancy state so the output is driven directly from a register and `in_ready` uses a state bit instead of a multi-bit occupancy comparison, improving setup slack while preserving the FIFO’s cycle behavior.

## Instruction for generator

In `sync_fifo_core`, replace the binary `occupancy` counter and `(occupancy < DEPTH)` comparison with a parameterized one-hot occupancy state for counts 0 through `DEPTH`; derive `out_valid` and the not-full condition from that state, and retain `in_ready = not_full || out_ready`. Also apply the tried output-register transformation: drive `out_data` directly from a register and update it on accepted pushes and retiring pops so the oldest payload and stall stability remain exact. Preserve explicit pointer wrap, simultaneous full pop/push, synchronous reset, all supported `WIDTH`/`DEPTH` values, the top `// @latency 1` annotation, and every defined transfer age and handshake behavior.