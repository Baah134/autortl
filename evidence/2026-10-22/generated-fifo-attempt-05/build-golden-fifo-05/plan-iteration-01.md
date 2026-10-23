# PLAN — iteration 1

## Current state assessment

The baseline passes simulation and has valid routed metrics, but it is not timing-feasible: setup WNS is −0.931 ns while hold WHS is +0.091 ns. The failing path runs from `rd_ptr` through a `RAMD32` asynchronous read to `out_data[7]`; the baseline uses 13 LUTs and 6 FFs. Promotion first requires passing every verification and metric gate with setup and hold slack both nonnegative. A candidate may then replace this timing-infeasible best as a timing recovery, even if LUT use increases.

## Hypothesis

Replacing the dynamic-index distributed-RAM read path with a registered head word should remove the pointer-to-output read path and improve setup slack, at the cost of additional FFs and possibly LUTs.

## Instruction for generator

In the editable `sync_fifo` top only, replace the `sync_fifo_core` instance with equivalent three-entry shift-register FIFO logic so `out_data` is driven directly by the registered head word rather than an asynchronously indexed memory read. Preserve the exact ready/valid equations, synchronous active-high reset priority, one-cycle minimum transfer age, stable valid payload during stalls, and full simultaneous pop/push behavior; keep invalid `out_data` unspecified. Retain the top interface and add `// @latency 1`; leave the frozen child module untouched.