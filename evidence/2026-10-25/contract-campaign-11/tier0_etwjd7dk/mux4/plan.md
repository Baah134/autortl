# PLAN — iteration 1
## Current state assessment
The current design is timing-feasible at 10 ns, with 8 LUTs, 8 FFs, WNS 0.579 ns, and WHS 0.052 ns. The objective is strictly fewer LUTs while retaining timing feasibility and every defined cycle of behavior. Top numeric latency is unknown, so no numeric latency annotation is required.

## Hypothesis
Using 7-series MUXF7/MUXF8 primitives for the 4:1 data selection may reduce LUT use from 8 to 0, at the cost of 16 MUXF7 and 8 MUXF8 resources, with timing to be verified after routing.

## Instruction for generator
Replace the `case (sel)` data-selection pattern with two MUXF7 stages feeding one MUXF8 per output bit, selecting `a/b` and `c/d` with `sel[0]`, then selecting between those results with `sel[1]`. Keep the existing rising-edge output register and synchronous active-high reset, with reset taking priority and setting `y` to zero. Preserve the full 8-bit data paths and the exact selection behavior; do not add pipeline stages or a numeric latency annotation.