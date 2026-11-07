# PLAN — iteration 1
## Current state assessment

The verified incumbent meets timing at 325 LUTs, 52 FFs, WNS 0.087 ns, and WHS 0.202 ns, so this iteration must pass every gate and strictly reduce LUTs to improve the `minimize_luts` objective. The four unsigned 8×8 products currently use no DSP48s; the top’s numeric latency is unknown, and its existing registered cycle behavior must be preserved.

## Hypothesis

Inferring the four multipliers into DSP48s will reduce LUT use while leaving the pair and merge adders, register boundaries, and output behavior unchanged.

## Instruction for generator

In `dot4_pair01` and `dot4_pair23`, add the Xilinx `use_dsp = "yes"` synthesis attribute to each existing 16-bit product wire for the unsigned 8×8 multiplication. Keep the 17-bit pair sums and their synchronous resettable registers, the live `dot4_merge` instance and its full-width addition, and the final registered output unchanged. Preserve all current cycle behavior and do not add a numeric top latency annotation.