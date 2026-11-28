# PLAN — iteration 1
## Current state assessment
The incumbent is timing-feasible at 8 LUTs and 8 FFs, with routed WNS 0.579 ns and WHS 0.052 ns. The objective is strictly fewer LUTs while keeping timing feasible; the current top’s numeric latency is unknown, so preserve its existing registered behavior without inventing an annotation.

## Hypothesis
Implementing each 4:1 data mux with 7-series MUXF7/MUXF8 primitives may reduce LUT use while retaining the eight output registers, though the added mux stages could reduce setup slack.

## Instruction for generator
Replace the `case (sel)` data mux with, for each output bit, two MUXF7 stages selected by `sel[0]` and one MUXF8 stage selected by `sel[1]`; keep the existing synchronous reset behavior using FDRE synchronous reset or equivalent inference. Preserve the exact ports, one-cycle registered output, reset priority and behavior for all four `sel` values. Compare routed LUTs, WNS and WHS against the incumbent, and retain the candidate only if all verification gates pass and LUT count strictly decreases.