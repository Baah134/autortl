# PLAN — iteration 3

## Current state assessment

Iteration 1’s DSP-directed implementation is the verified best at 20 LUTs, 20 FFs, and four DSP48s, with setup WNS 0.105 ns and hold WHS 0.18 ns. Iteration 2’s pair-sum rewrite passed behavior and timing but did not reduce LUTs, so it was correctly rejected against the feasible incumbent. The current seed still has two 17-bit stage-one partial-sum registers; the objective is strict LUT reduction, with all simulation, routed metric, setup, and hold gates mandatory.

## Hypothesis

Registering the complete 18-bit dot product in stage one instead of two 17-bit partial sums may reduce state-update and arithmetic logic, at the cost of a longer input-to-register path that could threaten timing closure.

## Instruction for generator

In the editable top’s elastic pipeline, replace `stage1_sum01` and `stage1_sum23` with one 18-bit stage-one result register, computed from all four explicitly unsigned 8×8 products with sufficient intermediate width to preserve carries. Keep the existing stage-two result register, valid-slot flow control, synchronous active-high reset behavior, and `// @latency 2`; transfer the registered stage-one result to stage two only under `stage2_ready`, preserving stall stability and simultaneous retire/advance/replace behavior. Do not change the ports or handshake equations; retain this candidate only if the unchanged testbench and all routed setup/hold and metric-integrity gates pass, and LUT use is strictly below the 20-LUT incumbent.