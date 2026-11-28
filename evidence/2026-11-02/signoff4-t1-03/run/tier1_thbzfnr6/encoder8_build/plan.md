# PLAN — iteration 1
## Current state assessment
The verified incumbent is timing-feasible at 6 LUTs and 4 FFs, with routed WNS 0.528 ns and WHS 0.009 ns; the objective is a strict LUT reduction, with FFs as the tie-breaker. The seed registers the 3-bit index and valid flag, and the top has known latency 1, so preserve those registers and the matching `// @latency 1` annotation. No prior proposal outcomes are available.

## Hypothesis
Factoring the priority decision into shared high-bit and lower-bit prefix terms may reduce LUT use versus the synthesized priority-mux chain while keeping the same four FFs and cycle behavior.

## Instruction for generator
Replace the sequential `if/else if` priority chain with explicit combinational Boolean equations for the three index bits, sharing prefix terms for `request[7:4]`, `request[7:6]`, and `request[7:2]`; register those bits and `request != 0` in the existing synchronous active-high reset block. Preserve the zero-request index value, highest-set-bit selection, registered outputs, and reset behavior, and keep the top’s `// @latency 1` annotation. This is a LUT-reduction experiment, not an assumed win: retain it only if the unchanged verification gates pass and routed LUTs are strictly lower than the incumbent.