# PLAN — iteration 1

## Current state assessment

The incumbent is timing-feasible at 8 LUTs and 8 FFs, with routed WNS 0.579 ns and WHS 0.052 ns. The seed is a registered 4:1, 8-bit mux with synchronous active-high reset; it has no parameters, and its top-level numeric latency is unknown. With no prior trials, the first iteration should target the `case` mux’s LUT cost while preserving its registered output and exact cycle behavior.

## Hypothesis

A one-hot decode of `sel` with masked data terms and a shared bitwise OR may map to fewer LUTs than the `case` mux while retaining the same 8 output FFs and timing feasibility.

## Instruction for generator

Replace the `case` selection with four mutually exclusive `sel` equality terms, mask `a`, `b`, `c`, and `d` with their respective terms, then OR the masked 8-bit values into the registered `y` input. Keep the existing `posedge clk` process and synchronous active-high reset to zero; on every non-reset edge, update `y` from the selected input with no added state or hold condition. Preserve all ports and widths, and do not add a numeric latency annotation because the current top latency is unknown.