# PLAN — iteration 7

## Current state assessment

Iteration 6 is the verified incumbent at 78 LUTs and 202 FFs, with setup WNS +1.651 ns and hold WHS +0.106 ns. Since timing is feasible, promotion requires a strict improvement in the `minimize_luts` objective; iterations 4 and 5 increased LUT use and were rejected. The seed already contains iteration 6’s accepted ready logic. The advisor’s missing I/O delay note does not change the fixed constraints or internal timing gates.

## Hypothesis

Express the existing two-bit saturation overflow test as a sign-bit mismatch check to potentially reduce LUTs while preserving the rounded result exactly.

## Instruction for generator

In `fir16_sym_core`, replace the `always @(*)` saturation branches that compare `rounded[16:15]` against `2'b01` and `2'b10` with a check for `rounded[16] != rounded[15]`; select positive saturation when `rounded[16]` is 0 and negative saturation when it is 1. When the bits match, keep `rounded[15:0]` unchanged. Preserve the five-stage handshake, registered outputs, reset behavior, and top `// @latency 5`; evaluate against all fixed gates and promote only if routed LUTs strictly improve over 78 while timing remains feasible.