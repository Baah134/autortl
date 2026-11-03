# PLAN — iteration 3
## Current state assessment
Iteration 2 is the verified, timing-feasible best at 24 LUTs and 42 FFs, with WNS 0.107 ns and WHS 0.126 ns. The objective is now a strict LUT reduction, or fewer FFs at the same LUT count; preserve the top’s known `// @latency 1` annotation and all FIFO behavior.

## Hypothesis
Replacing the occupancy counter and its full comparison with a registered full flag may reduce LUT use by removing count update and comparison logic, while pointer equality supplies the empty condition.

## Instruction for generator
In `packet_fifo_core`, replace `occupancy` with a `full` register: derive empty from `read_ptr == write_ptr` and `!full`, use `!full || out_ready` for `in_ready`, and use `!empty` for `out_valid`. Update `full` from accepted push/pop events, including full simultaneous pop/push, and keep explicit pointer wrap at `DEPTH-1` for every supported depth. Preserve the existing memory payload path and all top ports, reset behavior, stall stability, minimum transfer age, and the top’s `// @latency 1`; retain this candidate only if routed reports show a strict objective improvement and all verification and timing gates pass.