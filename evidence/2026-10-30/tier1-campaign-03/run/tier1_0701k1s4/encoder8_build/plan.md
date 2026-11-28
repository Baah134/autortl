# PLAN — iteration 1
## Current state assessment

The 8-bit encoder currently uses 6 LUTs and 4 FFs, and its timing is feasible at the 10 ns clock period (WNS 0.528 ns, WHS 0.009 ns). The objective is a strict LUT reduction; there are no prior iteration results to avoid repeating.

## Hypothesis

Replacing the frozen core instance with shared group-prefix logic in the editable top may reduce the encoder’s LUT count while keeping the same registered outputs and reset behavior.

## Instruction for generator

Replace the transparent `priority_encoder8_core` instance with local logic that factors request bits into upper and lower 4-bit priority groups, shares group-valid and prefix terms, and computes the highest-set-bit index plus `valid`. Register `index` and `valid` on `posedge clk` with the existing synchronous active-high reset, preserving the one-cycle behavior and declare `// @latency 1`. Target fewer than 6 LUTs with 4 FFs; preserve all 256 request cases and between-edge output holds.