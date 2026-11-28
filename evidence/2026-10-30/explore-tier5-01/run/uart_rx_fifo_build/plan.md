# PLAN — iteration 3
## Current state assessment
Iteration 2 is the verified, timing-feasible incumbent at 66 LUTs, 59 FFs, WNS 0.548 ns and WHS 0.051 ns. Since both it and any candidate must meet timing, the `minimize_luts` objective requires a strict LUT reduction; the current top’s numeric latency is unknown, so no top latency annotation is required.

## Hypothesis
Replacing the UART data register’s variable-index bit write with a fixed-direction shift on each data-bit decision should reduce decoder and write-selection LUTs while preserving the received byte.

## Instruction for generator
In `uart_rx_core`, replace `rx_shift[bit_index - 1'b1] <= majority_vote` in the data-bit branch with a right shift that inserts `majority_vote` at bit 7; after the eighth data decision, the register holds the byte in normal bit order. Keep the existing `bit_index` qualification, sample/decision edges, start-of-frame clear, reset behavior, and stop-bit capture unchanged. Preserve behavior for every supported `OVERSAMPLE_DIV`, then rely on the frozen integration testbench and routed reports to establish correctness, strict LUT improvement, and setup/hold closure.