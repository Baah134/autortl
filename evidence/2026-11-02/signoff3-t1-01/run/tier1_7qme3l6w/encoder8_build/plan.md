# PLAN — iteration 1
## Current state assessment

The incumbent uses 6 LUTs and 4 FFs on `xc7a35tcpg236-1`, with routed WNS 0.528 ns and WHS 0.009 ns, so timing is feasible. The minimize-LUT objective requires a strict LUT reduction, or equal LUTs with fewer FFs; the four registered output bits are required to preserve the defined cycle behavior.

## Hypothesis

Factoring the priority encoder into shared high- and low-nibble nonzero terms may let Vivado map the encoder with fewer than 6 LUTs while retaining the 4 output registers and one-cycle behavior.

## Instruction for generator

Replace the serial `if/else` priority chain in `priority_encoder8_core` with grouped 4-bit priority equations: compute shared nonzero terms for each nibble, encode each nibble’s highest set bit, and select the high nibble whenever it is nonzero. Preserve synchronous active-high reset, registered `index` and `valid`, exact priority and zero-request results, and the top’s `// @latency 1` annotation. This is an area hypothesis only: retain the candidate only if it passes all gates and improves the objective against the incumbent.