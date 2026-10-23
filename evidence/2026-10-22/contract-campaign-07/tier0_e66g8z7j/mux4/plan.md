# PLAN — iteration 1
## Current state assessment
The registered 8-bit 4:1 mux passes the supplied simulation and has valid baseline metrics: 8 LUTs, 8 FFs, WNS 0.579 ns and WHS 0.052 ns on xc7a35tcpg236-1 at 10 ns. Timing is feasible, so `minimize_luts` requires a strict reduction below 8 LUTs while retaining timing feasibility and every defined cycle behavior. Top numeric latency is unknown; the missing annotation is not a failure and does not justify adding one.

## Hypothesis
Replace the data-select logic with 7-series MUXF7/MUXF8 primitives, which may implement each 4:1 bit selection without LUTs and reduce LUT use below 8 while preserving the existing 8 registered outputs.

## Instruction for generator
In `mux4`, replace the `case (sel)` data-selection pattern with two MUXF7 selections per output bit feeding one MUXF8, using `sel` for the same 4:1 mapping of `a`, `b`, `c`, and `d`. Keep the existing rising-edge register and synchronous active-high reset to zero unchanged; preserve the exact port interface and one-cycle registered behavior. Do not add a numeric latency annotation. Promote the candidate only if the frozen checks pass and valid routed evidence shows WNS and WHS at least zero and LUT use strictly below 8.