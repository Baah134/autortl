# PLAN — iteration 2

## Current state assessment
Iteration 1 is the verified best, with WNS −0.102 ns and WHS 0.089 ns, so timing remains infeasible. The advisor trial improved WNS to −0.063 ns and kept WHS positive, but its worst path shifted to `occupancy` → `out_valid`; adding another change to `in_ready` alone would repeat an experiment that still missed setup.

## Hypothesis
A registered nonempty flag driving `out_valid` directly can remove the occupancy decode from the output path and improve routed setup slack while preserving the FIFO’s cycle behavior.

## Instruction for generator
In `sync_fifo_core`, add a `nonempty` state bit, synchronously clear it on `rst`, and update it from the accepted `push` and `pop` events so it always tracks whether occupancy is nonzero; drive `out_valid` directly from this bit. Keep the occupancy counter and head-data logic, and preserve the current combinational `in_ready = (occupancy < DEPTH) || out_ready` behavior, including full simultaneous pop/push. Preserve the top’s `// @latency 1` annotation and verify reset, empty capture, final pop, stalls, and parameterized depths.