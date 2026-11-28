# PLAN — iteration 4
## Current state assessment
The incumbent is already timing-feasible at 3 LUTs, 4 FFs, WNS 0.57 ns, and WHS 0.057 ns. Iterations 1 and 3 found no LUT or FF gain with an inline binary counter; iteration 2’s Johnson encoding increased both. With three consecutive iterations without improvement, another equivalent binary rewrite is unlikely to help, and this candidate must strictly reduce LUTs to replace the feasible incumbent.

## Hypothesis
A 3-bit de Bruijn shift-state may reduce counter logic by replacing binary increment and terminal comparison with shifts and a feedback function, while retaining four state bits; any LUT reduction is uncertain and must be measured after routing.

## Instruction for generator
Inline the frozen child behavior in `debouncer_top` and replace the binary counter with a 3-bit progression through `000, 001, 010, 101, 011, 111, 110, 100`, returning to `000` on the eighth differing sample. Clear progress whenever `noisy` equals the registered `clean`; synchronously reset both state and `clean` to zero, and update `clean` only when the prior progress state is `100` and `noisy` differs from `clean`. Preserve `// @latency 0` and accept the candidate only if it passes every fixed gate and routed LUT usage is strictly below 3.