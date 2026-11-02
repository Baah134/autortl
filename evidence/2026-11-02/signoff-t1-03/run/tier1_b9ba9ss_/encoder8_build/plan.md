# PLAN — iteration 1

## Current state assessment

The incumbent uses 6 LUTs and 4 FFs, passes simulation, and meets setup and hold timing at 10 ns; there is no register-to-register path. Timing is already feasible, so promotion requires a strict LUT reduction under `minimize_luts` (or equal LUTs with fewer FFs). The top must retain its registered outputs, synchronous active-high reset, exact one-cycle behavior, and `// @latency 1` annotation.

## Hypothesis

Replacing the priority `if/else` chain with grouped Boolean equations for the three index bits and `valid` may let Vivado map the encoder into fewer than 6 LUTs while keeping the same four output registers.

## Instruction for generator

In `priority_encoder8_core`, replace the descending `if/else` index selection with explicit equations: `index[2]` is the OR of `request[7:4]`; `index[1]` selects requests 7/6, or requests 3/2 when no upper-half request is set; `index[0]` is true for request 7, request 5 when 7/6 are clear, request 3 when 7:4 are clear, or request 1 when 7:2 are clear. Keep `valid` as the OR reduction of all request bits, and register these results with the existing reset behavior and output registers. Preserve the top interface and its `// @latency 1` annotation; add no state or cycles. This is a LUT-count hypothesis, not a guaranteed gain, so retain the candidate only if the unchanged simulation and all routed metric gates pass and the objective improves.