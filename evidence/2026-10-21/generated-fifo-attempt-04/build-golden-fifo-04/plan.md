# PLAN — iteration 2
## Current state assessment
Iteration 1’s three-register FIFO passed simulation and the parameter matrix, but missed the required `// @latency 1` declaration and setup timing (WNS −0.289 ns); its 21 LUTs also exceeded the 13-LUT baseline. The advisor trial narrowed the remaining timing risk to the binary occupancy comparison feeding `in_ready` (WNS −0.016 ns), while the baseline’s worst path was the read pointer to `out_data`. Timing feasibility is the first gate, so this iteration should target that ready path and retain the direct `payload0` output from the trial architecture.

## Hypothesis
Replacing the occupancy comparison on `in_ready` with a registered `not_full` state bit will shorten the ready path and may close timing, while preserving FIFO behavior; routed WNS and WHS will determine whether it succeeds.

## Instruction for generator
In `sync_fifo`, keep the three 8-bit payload registers and direct `out_data = payload0` mapping, but add a `not_full` state bit reset to 1 and drive `in_ready = not_full || out_ready` instead of comparing occupancy to 3. Update `not_full` on the same push/pop cases as occupancy so it clears only when a push fills the FIFO and sets when a pop frees a full FIFO; hold it on simultaneous push/pop and idle, preserving full simultaneous transfers and all existing queue behavior. Add `// @latency 1`; preserve the interface, synchronous active-high reset, and observable cycles, then judge the candidate on the fixed simulation and routed setup/hold gates.