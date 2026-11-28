# PLAN — iteration 3

## Current state assessment

Iteration 1 established a timing-feasible best at 65 LUTs and 64 FFs, so this iteration must pass every gate and strictly reduce LUTs to improve the incumbent. Iteration 2’s parameter-derived frame-offset width proposal was rejected for LUT growth; do not repeat it. The current top’s numeric latency is unknown, so no top latency annotation is required.

## Hypothesis

In `uart_rx_core`, shifting each sampled data bit into `frame_data` instead of dynamically indexing it by `bit_index` may remove write-decoder LUTs while keeping the register count roughly constant.

## Instruction for generator

In `uart_rx_core`, replace the `frame_data[bit_index - 1'b1] <= majority` variable-index write in the data-bit decision branch with a right shift that inserts `majority` at bit 7; keep the existing start-bit, stop-bit, and decision-cycle conditions. Preserve the reset and frame-start clear, and verify that the final byte remains LSB-first for every supported `OVERSAMPLE_DIV`. Keep the iteration 1 FIFO output register behavior so the routed timing closure is retained; do not change the top interface or add latency.