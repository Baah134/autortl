# PLAN — iteration 1
## Current state assessment
The seed is an 8-bit registered 4:1 mux with synchronous active-high reset. The incumbent is timing-feasible at WNS 0.579 ns and WHS 0.052 ns, so this iteration must strictly reduce LUTs to improve the `minimize_luts` objective; 8 LUTs and 8 FFs leave little room, and there is no prior trial evidence to avoid repeating.

## Hypothesis
A balanced 2:1 mux tree may let Vivado use 7-series MUXF7/MUXF8 resources instead of one LUT per output bit, reducing LUT use while preserving the output register and reset behavior.

## Instruction for generator
Replace the `case (sel)` data selection with a balanced tree of 2:1 selections: first select `a/b` and `c/d` using `sel[0]`, then select between those results using `sel[1]`. Keep the existing clocked `if (rst) y <= 8'd0; else ...` structure unchanged so reset remains synchronous and `y` remains registered. Preserve the exact port interface and cycle behavior; do not add a latency annotation because current top latency is unknown.