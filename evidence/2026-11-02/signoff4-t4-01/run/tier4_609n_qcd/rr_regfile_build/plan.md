# PLAN — iteration 2
## Current state assessment

The incumbent is timing-feasible at 40 LUTs and 90 FFs. Iteration 1’s explicit cyclic-priority loop with a separate winner `case` passed simulation and timing but rose to 46 LUTs, so it did not improve the LUT objective. The top’s numeric latency is unknown; preserve its observed cycle behavior without adding a numeric latency annotation.

## Hypothesis

Using one-hot winner terms both to select the grant and to mask/OR the address and data inputs may remove the binary winner decode and reduce LUTs while retaining the existing registered outputs and timing feasibility.

## Instruction for generator

Change only `rr_arbiter4`’s winner selection and address/data mux: form mutually exclusive one-hot winner terms directly from `last` and `req` in round-robin order, then use those same terms to produce the registered grant and bitwise masked-OR address/data. Do not use the iteration 1 pattern of a separate explicit cyclic scan followed by `case (winner)`; keep `last` binary and update it to the selected winner. Preserve reset, idle outputs and pointer hold, all registered behavior, round-robin order, and the top interface; retain the regfile implementation.