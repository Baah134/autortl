# PLAN — iteration 1

## Current state assessment

The baseline passes simulation and has retained routed evidence of 8 LUTs, 8 FFs, WNS 0.579 ns, and WHS 0.052 ns on the specified device and constraints. Timing is feasible; the objective therefore requires strictly fewer than 8 LUTs. The current registered 8-bit, four-input mux maps to one LUT per output bit, so there may be little room to reduce LUT use. Top numeric latency is unknown; preserve the existing registered behavior without adding an annotation.

## Hypothesis

Replacing the `case` mux with a packed-vector variable part-select may let Vivado map selection more compactly, but the hypothesis succeeds only if routed LUT use drops below 8 and every required gate passes.

## Instruction for generator

In `mux4`, replace the `case (sel)` data selection with a variable part-select from the packed vector `{d, c, b, a}`, using `sel` to select the same 8-bit input; keep the existing clocked block and synchronous active-high reset. Preserve the 8-bit registered output and its exact cycle behavior for all four `sel` values. Do not add a latency annotation; evaluate the unchanged verification gates and compare routed LUT use against the incumbent’s 8 LUTs.