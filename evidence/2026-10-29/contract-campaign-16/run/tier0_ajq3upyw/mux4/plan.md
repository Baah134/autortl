# PLAN — iteration 1

## Current state assessment

The seed is an 8-bit registered 4:1 mux with synchronous active-high reset. The incumbent’s routed metrics show 8 LUTs, 8 FFs, WNS 0.579 ns, and WHS 0.052 ns; timing is feasible, so promotion requires a strict LUT reduction. One LUT per output bit is already the natural lower bound for eight independent mux outputs. The top latency is unknown, so no numeric `@latency` annotation is required; preserve the existing cycle behavior and reset priority.

## Hypothesis

Rewriting the selection as a packed-vector variable part-select may preserve the eight-LUT mapping, but is unlikely to reduce LUTs below the one-per-output floor.

## Instruction for generator

Replace the `case (sel)` selection with a variable part-select from `{d, c, b, a}`, indexed by `sel` to select the same 8-bit input; keep the synchronous reset as the outer priority branch. Preserve the registered `y` output and all port names and widths, and do not add a latency annotation. Treat any equal or higher LUT count as no objective improvement; promotion still requires all fixed simulation, synthesis, routed metric, setup, and hold gates to pass.