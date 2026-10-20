# PLAN — iteration 1
## Current state assessment
The baseline passes simulation and reports 8 LUTs, 8 FFs, WNS 0.579 ns, and WHS 0.052 ns on the xc7a35tcpg236-1 at a 10 ns clock. The objective requires fewer than 8 LUTs while preserving the synchronous active-high reset and one-cycle registered output; the reported metrics leave little apparent area to remove.

## Hypothesis
Rewriting the 4:1 `case (sel)` as nested 2:1 conditional muxes may help Vivado map selection onto the 7-series MUXF7/MUXF8 resources and reduce LUT use, though the baseline may already map optimally.

## Instruction for generator
Replace the `case (sel)` that selects `a`, `b`, `c`, or `d` with nested 2:1 conditional expressions controlled by `sel[0]` and `sel[1]`, preserving the same four input-to-select mappings. Keep the existing `if (rst)` synchronous reset to zero and the same `posedge clk` assignment to `y`. Do not add registers or change latency.