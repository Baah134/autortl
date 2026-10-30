# PLAN — iteration 1

## Current state assessment
The 8-bit output is registered on `posedge clk` with synchronous active-high reset; the `case` selects one of four 8-bit inputs every non-reset cycle. The incumbent is timing-feasible at WNS 0.579 ns and WHS 0.052 ns, with 8 LUTs and 8 FFs. Since the objective is strict LUT reduction, an equal-LUT result is not an improvement; one LUT per output bit is already a plausible mapping for this four-input mux.

## Hypothesis
Replacing the `case` with decoded, bitwise-masked input terms may expose a mapping that uses fewer than 8 LUTs while retaining the same registered output and reset behavior, though the current mapping may already be at the practical LUT floor.

## Instruction for generator
Replace the `case (sel)` data-selection branch with four mutually exclusive `sel` comparisons, AND each input bus with its corresponding replicated comparison bit, and OR the masked buses into the value assigned to `y`. Keep the existing `posedge clk` block and synchronous `if (rst) y <= 8'd0;` priority exactly intact. Preserve all four selector mappings and the registered output; do not add an annotation because the current top numeric latency is unknown.