# PLAN — iteration 4
## Current state assessment
The verified incumbent uses 3 LUTs and 4 FFs and meets timing at WNS 0.57 ns and WHS 0.167 ns. Iteration 2 established the incumbent; iteration 3’s LFSR counter proposal was rejected. Since the incumbent is timing-feasible, promotion requires strictly fewer LUTs, or the same LUT count with fewer FFs, plus every verification and routed-report gate.

## Hypothesis
Encoding the debounce interval as a 3-bit countdown with zero as the idle state may map its terminal detection and update logic into fewer LUTs while keeping the 4-FF state and exact debounce cycles.

## Instruction for generator
In `debouncer_top`, keep `clean_reg` and the 3-bit counter, but replace the binary up-counter and `count == 3'd7` saturation branch with a countdown: reset the count to zero when `noisy == clean_reg`, load `3'd7` on the first differing sample while idle, and decrement on subsequent differing samples. When the prior count is `3'd1`, update `clean_reg` to `noisy` and return the count to zero, so the output changes on the eighth consecutive differing sample. Preserve synchronous active-high reset, registered `clean`, the exact interface and `// @latency 0`; retain the candidate only if all gates pass and routed metrics strictly improve on the incumbent objective.