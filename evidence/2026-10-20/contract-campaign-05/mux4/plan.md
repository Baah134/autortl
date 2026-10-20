# PLAN — iteration 1
## Current state assessment
The baseline is an 8-bit, synchronous 4:1 mux with an active-high synchronous reset and registered output; its exact numeric latency is unknown, so preserve its observable cycle behavior. Baseline evidence reports 8 LUTs, 8 FFs, WNS 0.579 ns, and WHS 0.052 ns, with simulation passing. The LUT count is already small; any gain must come from Vivado mapping the mux into dedicated 7-series MUXF resources, and must be confirmed in routed reports.

## Hypothesis
Rewriting the selector as an explicit two-level mux tree may reduce LUT use by encouraging MUXF7/MUXF8 mapping while preserving the existing reset and output register.

## Instruction for generator
Replace the `case (sel)` that assigns `y` with a nested conditional mux tree encoding `sel[1]` as the outer choice and `sel[0]` as the inner choice, preserving the mapping 00→a, 01→b, 10→c, 11→d. Keep the existing `posedge clk` block, active-high synchronous reset to zero, and registered `y` assignment unchanged. Do not add or remove registers or change any ports.