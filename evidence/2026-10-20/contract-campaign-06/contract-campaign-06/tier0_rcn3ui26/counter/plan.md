# PLAN — iteration 1
## Current state assessment
The verified baseline uses 55 LUTs and 37 FFs on xc7a35tcpg236-1, with routed WNS 0.494 ns and WHS 0.113 ns; simulation passes. The objective is to reduce LUTs while preserving the counter’s exact observable cycles. Latency is unannotated and unknown. The source contains a dead register and a redundant increment temporary, but synthesis may already remove them, so this plan targets the explicit all-ones comparison and count selection.

## Hypothesis
Using the carry-out of a `WIDTH+1` increment to detect wrap may reduce LUT use by sharing the increment’s carry chain, while preserving count and overflow behavior.

## Instruction for generator
Replace the enabled-count branch’s all-ones comparison and conditional zero-versus-`count_next` assignment with a `WIDTH+1` unsigned increment whose carry-out determines `overflow` and whose low `WIDTH` bits determine `count`. Preserve synchronous reset priority, load-over-enable priority, disabled-cycle count and overflow holds, and the registered threshold flags exactly. Keep all ports, parameters, widths, and observable cycle behavior unchanged.