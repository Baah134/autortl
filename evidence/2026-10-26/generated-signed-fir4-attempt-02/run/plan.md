# PLAN — iteration 3
## Current state assessment
The verified incumbent is timing-feasible at 84 LUTs with WNS 0.147 ns, so iteration 3 must reduce LUTs while retaining nonnegative setup and hold slack. Iteration 2 reduced LUTs to 81 but failed setup timing; its trial’s critical path ended at `in_ready`, so changing the ready logic again risks losing timing feasibility.

## Hypothesis
Replacing the wide constant-multiply FIR expression with width-controlled signed shift-add terms and a balanced sum may reduce LUT use without disturbing the timing-feasible ready path.

## Instruction for generator
Keep the occupancy/full readiness logic and all valid, data, history, reset, and pipeline registers unchanged. Change only the `fir_value` datapath: express the four constant-coefficient products using signed shifts and adds, size each partial to preserve its full signed range, sign-extend before a balanced final sum, and retain the exact signed 13-bit result. Preserve `// @latency 3` and all defined cycle behavior; promotion still requires the frozen checks and routed WNS and WHS of at least zero.