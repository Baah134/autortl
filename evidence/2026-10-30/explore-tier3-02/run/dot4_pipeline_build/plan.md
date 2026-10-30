# PLAN — iteration 1

## Current state assessment
The incumbent passes simulation and meets timing at 10 ns (WNS 0.087 ns, WHS 0.202 ns), using 325 LUTs, 52 FFs, and no DSPs. The objective is strict LUT reduction once verification and timing gates pass; the current top’s numeric latency is unknown, so no numeric top annotation is required. There are no prior trial outcomes to avoid.

## Hypothesis
Mapping the four unsigned 8×8 multipliers to DSP48s should reduce LUT use, at the cost of four DSPs and potentially different routing or timing.

## Instruction for generator
Replace the two pair-module instances with equivalent local unsigned 8×8 multiply and pair-add logic, marking the four multiplication operators for DSP inference; register each 17-bit pair sum on `posedge clk` with the existing synchronous active-high reset behavior. Keep the `dot4_merge` instance unconditional, and connect its output to `dot_result`; preserve the existing two-edge observable behavior, one-sample-per-edge throughput, and full unsigned arithmetic widths. Leave the top unannotated because its authoritative numeric latency is unknown.