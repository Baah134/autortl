# PLAN — iteration 1

## Current state assessment

The incumbent passes simulation and has positive routed setup and hold slack (WNS 0.528 ns, WHS 0.009 ns). It uses 6 LUTs and 4 FFs on the xc7a35tcpg236-1, so timing is feasible and this iteration must strictly reduce LUTs to improve the minimize_luts objective; equal LUT use cannot improve the objective because the four registered output bits are already present.

## Hypothesis

Expressing priority as shared prefix-dominance terms may let Vivado map the encoder with fewer than 6 LUTs while retaining the same four output registers and timing feasibility.

## Instruction for generator

Replace the descending `if/else` priority chain that assigns `index_reg` with explicit winner terms: each request bit wins only when set and every higher-priority bit is clear, then OR the winning terms into the three encoded index bits. Keep the `valid_reg <= |request` reduction, synchronous active-high reset, registered outputs, exact one-cycle behavior, and the top module’s `// @latency 1` annotation. Preserve index zero for an all-zero request and highest-set-bit priority for every nonzero pattern; this is an area hypothesis, so retain the candidate only if all gates pass and routed LUT use is strictly below 6.