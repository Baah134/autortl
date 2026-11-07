# PLAN — iteration 3
## Current state assessment
The incumbent is timing-feasible at 20 LUTs and 20 FFs, so iteration 3 must strictly reduce LUTs without losing setup or hold closure to improve the minimize-LUTs objective. Iteration 1’s four DSP-mapped multipliers were accepted; iteration 2’s DSP attributes on the input pair sums did not improve the incumbent. The top latency is known to be 2 cycles and requires `// @latency 2`.

## Hypothesis
Mapping the registered partial-sum addition to a DSP48 may replace its LUT carry logic with DSP arithmetic and reduce LUT use, at the cost of one DSP.

## Instruction for generator
Keep the four multiplier `use_dsp = "yes"` attributes and the iteration 2 input pair-sum implementation; add `(* use_dsp = "yes" *)` to the 18-bit `partial_sum` addition of the registered `partial_lo` and `partial_hi`. Preserve the existing 18-bit unsigned carry behavior and capture `result` under the same `stage2_ready` and `v1` conditions, without changing pipeline registers, handshake logic, synchronous reset, or top interface. Retain the candidate only if the unchanged integration testbench and all evidence gates pass, routed WNS and WHS remain nonnegative, and LUTs strictly decrease versus the incumbent.