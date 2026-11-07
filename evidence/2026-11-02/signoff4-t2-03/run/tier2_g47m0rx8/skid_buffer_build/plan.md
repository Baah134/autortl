# PLAN — iteration 2

## Current state assessment

Iteration 1 was accepted as a timing recovery, with routed WNS 0.146 ns and 19 FFs; the current verified incumbent is timing feasible at 11 LUTs and 19 FFs. Since the objective is `minimize_luts`, iteration 2 needs fewer than 11 LUTs to improve the incumbent, or equal LUTs with fewer FFs. The seed stores occupancy plus a registered valid bit, so its state includes a redundant nonempty indication.

## Hypothesis

Replace the occupancy counter with registered `valid` and `full` flags to remove redundant state decoding and potentially reduce LUT use while preserving FIFO behavior and registered `out_valid`.

## Instruction for generator

In `skid_buffer_core`, replace the 2-bit `occupancy` state with a `full` flag and reuse `out_valid_reg` as the registered nonempty flag; drive `in_ready` from `!full || out_ready` and keep `out_valid` driven directly by `out_valid_reg`. Update the two flags on push/pop combinations so empty, single-entry, full, simultaneous transfer, and full pop/push transitions preserve the exact two-entry FIFO behavior and stall stability. Preserve synchronous active-high reset, the one-cycle minimum transfer age, throughput, the top `// @latency 1` annotation, and all ports; evaluate against the incumbent’s 11 LUTs and 19 FFs with every required simulation, timing, hold, and metric gate.