# PLAN — iteration 1
## Current state assessment

The routed incumbent is timing-feasible at 6 LUTs and 8 FFs, with WNS 0.424 ns and WHS 0.226 ns. The objective is strictly fewer LUTs, so a candidate must pass every verification and metric gate and use fewer than 6 LUTs to improve the incumbent. The top already declares the required `// @latency 1`; its current behavior is synchronous active-high reset, modulo-256 increment when enabled, and hold otherwise.

## Hypothesis

Inlining the counter and using `enable` as the incrementer’s addend may reduce LUT use by folding the enable decision into the carry path while preserving the existing register count and timing feasibility.

## Instruction for generator

Replace the transparent `counter8_core` instance in `counter8` with an 8-bit registered counter that synchronously clears to zero on `rst` and otherwise updates as `count_reg <= count_reg + enable`, preserving hold when `enable` is low. Keep the exact ports, clock, reset priority, registered output behavior, and `// @latency 1` annotation. This is an experiment: retain it only if the unchanged verification gates pass, routed WNS and WHS remain nonnegative, and routed LUT use is strictly below 6.