# PLAN — iteration 1

## Current state assessment

The verified incumbent is timing-feasible at 325 LUTs, 52 FFs, WNS 0.087 ns, and WHS 0.202 ns, with four 8×8 multiplications mapped without DSP48 use. The objective is strictly fewer LUTs while preserving the two registered arithmetic stages and every defined reset and cycle behavior. The top’s numeric latency is unknown, so no numeric top annotation is required.

## Hypothesis

Inferring the four unsigned 8×8 products in DSP48E1 blocks can reduce LUT use at the cost of four DSP48s, with timing closure needing confirmation after routing.

## Instruction for generator

In `dot4_pair01` and `dot4_pair23`, replace each zero-extended 16×16 product expression with a direct unsigned 8×8 multiplication assigned to a 16-bit product wire, and apply `use_dsp = "yes"` to those four products. Keep both 17-bit pair-sum registers and the 18-bit registered `dot4_merge` output, including their synchronous active-high reset behavior. Preserve full product and addition carry widths; do not add or remove registers or add a numeric latency annotation to the top.