# PLAN — iteration 2
## Current state assessment
Iteration 1 is the verified best: it recovered timing with 328 LUTs, 54 FFs, and WNS 0.137 ns. The current objective is to reduce LUTs, so the next candidate must use fewer than 328 LUTs while preserving setup and hold feasibility and passing every behavioral and report gate.

## Hypothesis
Inferring the four unsigned 8×8 products in DSP48E1 blocks may reduce LUT use while leaving the two-stage elastic control and its cycle behavior intact.

## Instruction for generator
Inline the core logic in `elastic_dot4` and apply Xilinx `use_dsp = "yes"` inference to each of the four 16-bit unsigned multiplication results; keep the 17-bit pair sums and 18-bit final sum with their carry bits. Leave the two-slot valid, ready, reset, and registered output behavior unchanged, including the `// @latency 2` annotation. Check whether DSP inference lowers routed LUTs below 328 and still passes simulation, setup, hold, and metric-integrity gates.