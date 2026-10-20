# PLAN — iteration 1
## Current state assessment
The baseline uses 8 LUTs and 8 flip-flops, with 0.579 ns setup slack and 0.052 ns hold slack at 10 ns. The existing `case` already describes a compact 4:1 mux and may map to one LUT per output bit, so any LUT reduction is uncertain; reset behavior, one-cycle mapping, and routed timing must remain intact.

## Hypothesis
An explicit balanced mux expression may let Vivado map each output bit’s 4:1 selection into one LUT while preserving the synchronous reset.

## Instruction for generator
Replace the `case (sel)` assignment pattern with the explicit balanced selection `sel[1] ? (sel[0] ? d : c) : (sel[0] ? b : a)`. Keep the existing active-high synchronous reset to zero and the registered output `y` unchanged. Preserve the ports and one-cycle behavior.