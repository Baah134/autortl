# PLAN — iteration 1
## Current state assessment
The incumbent is timing-feasible at 8 LUTs and 8 FFs, with WNS 0.579 ns and WHS 0.052 ns. The seed implements a synchronous-reset, registered 4:1 mux; the top’s numeric latency is unknown, so no numeric latency annotation is required. Since the incumbent already passes timing, promotion requires a strict LUT reduction.

## Hypothesis
Replacing the `case` mux with a variable indexed part-select from a packed input bus may let Vivado map the 4:1 selection into fewer than 8 LUTs while preserving the registered output and synchronous reset.

## Instruction for generator
Replace the `case (sel)` data selection with a variable indexed part-select from a 32-bit packed bus ordered `{d, c, b, a}`, selecting the byte at offset `sel * 8`. Keep the existing `posedge clk` register and synchronous active-high reset to zero unchanged. Preserve the input ordering for every `sel` value; do not add latency or a numeric top latency annotation.