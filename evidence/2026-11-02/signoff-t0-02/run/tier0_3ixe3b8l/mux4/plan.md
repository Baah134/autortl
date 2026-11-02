# PLAN — iteration 1

## Current state assessment

The incumbent is timing-feasible at 8 LUTs and 8 FFs, with WNS 0.579 ns and WHS 0.052 ns. The current `case` implements a registered 4:1, 8-bit mux; each independent output bit needs its own selection logic, and the 8 FFs preserve the registered output behavior. The top’s numeric latency is unknown, so no numeric `@latency` annotation is required.

## Hypothesis

Rewriting the `case` as an indexed selection from a packed 32-bit input may let Vivado map the mux with no more than the current 8 LUTs, but a LUT reduction is uncertain because the incumbent is already near the one-LUT-per-output-bit floor.

## Instruction for generator

Replace the `case (sel)` selection with a packed concatenation of `{d, c, b, a}` and select the corresponding 8-bit slice using `sel`; keep the assignment in the existing `posedge clk` block. Preserve the synchronous active-high reset to zero, all ports, and the exact registered cycle behavior. Do not add a latency annotation; retain the candidate only if all gates pass and routed LUT usage is strictly below the incumbent, or LUT usage ties and FF usage is lower.