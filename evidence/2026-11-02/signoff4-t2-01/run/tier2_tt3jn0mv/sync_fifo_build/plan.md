# PLAN — iteration 2

## Current state assessment

Iteration 1 is the verified best: it closed setup and hold timing at WNS 0.153 ns and WHS 0.196 ns, using 21 LUTs and 27 FFs. Since timing is feasible, iteration 2 must strictly reduce LUTs, or match 21 LUTs while reducing FFs, to improve the `minimize_luts` objective. The current shift-register queue is already the accepted timing-recovery architecture.

## Hypothesis

Replacing the binary occupancy counter and separately registered `out_valid` with a thermometer occupancy vector may reduce LUTs by removing count increment/decrement and comparison logic while preserving the queue’s registered cycle behavior.

## Instruction for generator

In `sync_fifo_core`, replace the `occupancy` and `out_valid` state with a parameterized prefix-valid vector whose set bits represent occupied queue slots: derive `out_valid` from its head bit and `in_ready` from its terminal bit plus `out_ready`. Update that vector for push, pop, and simultaneous push/pop, and use it to select the first free queue slot for insertion; keep the shift-register payload queue and the existing registered transfer behavior. Preserve reset, full simultaneous pop/push, stall stability, explicit capacity for every supported `DEPTH`, and the top’s `// @latency 1` annotation; compare routed LUTs and FFs against the 21-LUT, 27-FF incumbent.