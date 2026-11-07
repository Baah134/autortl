# PLAN — iteration 1
## Current state assessment
The incumbent passes simulation and timing: 325 LUTs, 52 FFs, WNS 0.087 ns, WHS 0.202 ns, and no DSP48 use. The objective is strictly fewer LUTs once all gates pass. The top’s numeric latency is unknown; its missing annotation is not a failure, and the required cycle behavior must still be preserved.

## Hypothesis
Forcing the four unsigned 8×8 products into DSP48s will reduce LUT use while preserving the existing pair-sum registers and merge behavior.

## Instruction for generator
In `dot4_pair01` and `dot4_pair23`, apply Vivado’s `use_dsp = "yes"` inference directive to each 16-bit product from the unsigned 8×8 multiplications; keep the 17-bit pair additions and their synchronous resettable registers unchanged. Keep `dot4_merge` defined, live under the top, and exact over its full 17-bit input domain. Preserve all top-level ports and cycle behavior without adding a top latency annotation; promote only if simulation and report-integrity gates pass, routed WNS and WHS are both nonnegative, and LUT use is strictly below 325.