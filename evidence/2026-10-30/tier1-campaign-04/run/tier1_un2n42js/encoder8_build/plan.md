# PLAN — iteration 1

## Current state assessment

The verified incumbent uses 6 LUTs and 4 FFs, with setup WNS 0.528 ns and hold WHS 0.009 ns, so it is timing-feasible and the LUT objective requires a strict reduction. The editable seed is a transparent wrapper around the frozen registered core; no prior proposal outcomes are provided. The top must retain `// @latency 1`.

## Hypothesis

Inlining a factored two-group priority encoder may reduce LUT use below 6 by sharing upper-group detection and priority terms, while keeping the current four output registers and timing feasibility.

## Instruction for generator

Replace the child instance with top-level registered logic that divides `request` into upper and lower nibbles, uses the upper nibble whenever any of its bits are set, and encodes the highest set bit in the selected nibble. Register `index` and `valid` on `posedge clk`, preserving synchronous active-high reset to zero and the existing one-cycle behavior. Keep the interface and matching latency annotation; retain the candidate only if all gates pass and routed LUT use is strictly below 6.