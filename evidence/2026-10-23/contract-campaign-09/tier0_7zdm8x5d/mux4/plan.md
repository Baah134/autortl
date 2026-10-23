# PLAN — iteration 1

## Current state assessment

The baseline passes simulation and has positive routed setup and hold slack (WNS 0.579 ns, WHS 0.052 ns). It uses 8 LUTs and 8 FFs for eight independent registered output bits. Each bit implements a four-input selection function that fits one 6-input LUT, so 8 LUTs appears to be the practical floor; the current top’s numeric latency is unknown, and no numeric annotation is required.

## Hypothesis

Rewriting the `case (sel)` as an equivalent nested conditional mux may preserve one LUT per output bit and timing feasibility, but is unlikely to reduce LUTs below 8, so a result at 8 LUTs will not improve the stated objective.

## Instruction for generator

Replace only the `case (sel)` selection of `a`, `b`, `c`, or `d` with an equivalent nested conditional expression using `sel[1]` and `sel[0]`. Preserve the synchronous active-high reset to zero, the rising-edge registered output, all ports and widths, and the exact selection behavior for all four `sel` values. Do not add latency annotations or change cycle behavior; retain the candidate only if all gates pass and routed LUT usage is strictly below 8.