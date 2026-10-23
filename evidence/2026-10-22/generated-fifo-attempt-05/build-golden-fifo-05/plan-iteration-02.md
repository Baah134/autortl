# PLAN — iteration 2

## Current state assessment
Iteration 1 passed simulation and interface checks but failed timing feasibility: routed WNS was -0.289 ns and LUT use rose from 13 to 21. The baseline’s worst path runs from `rd_ptr` through distributed RAM to `out_data`; the trial evidence also shows `in_ready` can become a near-critical path. The objective is LUT minimization, but timing closure comes first.

## Hypothesis
Registering the FIFO head should remove the read-pointer-to-output mux path and improve setup slack, at the cost of additional FFs and potentially LUTs.

## Instruction for generator
In `sync_fifo`, replace the direct `sync_fifo_core` instance with a three-entry organization containing a registered head and a two-entry circular tail; on a push into an empty FIFO load the head, and on a pop with queued tail data promote the oldest tail word into the head. Handle simultaneous push/pop explicitly, including replacing the head when occupancy is one, while preserving the combinational ready rule, synchronous reset, registered output behavior, minimum transfer age, and `// @latency 1`. Retain the existing tail pointer wrap and occupancy behavior needed for the default depth, and assess the candidate against routed WNS, WHS, and LUT metrics before promotion.