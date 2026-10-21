# PLAN — iteration 2
## Current state assessment
Iteration 1 passed functional and tool gates but was rejected: routed WNS remained −0.905 ns and LUT use rose to 14 from the best’s 13. The baseline is also setup-infeasible at −0.931 ns, with WHS +0.091 ns. The objective is to establish timing feasibility first, then require a strict LUT reduction once both designs are timing-feasible; the critical path is not identified in the supplied evidence.

## Hypothesis
Replacing the depth-3 binary read and write pointers with one-hot pointers may shorten pointer update and memory selection logic enough to improve routed setup slack, at the cost of two additional FFs; routed WNS and WHS will determine whether it helps.

## Instruction for generator
Replace the `sync_fifo_core` instance in `sync_fifo` with inline logic specialized to its fixed 8-bit, depth-3 interface. Use three-bit one-hot read and write pointers to select the same circular-buffer entries, with explicit per-entry write enables and a one-hot masked-OR read mux; retain occupancy-based ready/valid, push/pop, synchronous reset, and memory hold behavior. Preserve exact observable cycle behavior, including `out_data` selection when empty and simultaneous push/pop, and add no pipeline stages or clocks.