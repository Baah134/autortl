# PLAN — iteration 2
## Current state assessment
Iteration 1 is the verified best: 70 LUTs, 64 FFs, WNS 0.55 ns and WHS 0.113 ns, so setup and hold timing are feasible. The objective is now strictly fewer LUTs than 70; equal LUTs qualify only with fewer FFs. The current top’s numeric latency is unknown, so no numeric top annotation is required.

## Hypothesis
Shifting each received data bit into the existing `rx_shift` register instead of dynamically indexing it may reduce LUT use without adding registers or changing the registered outputs.

## Instruction for generator
In `uart_rx_core`, replace the variable bit-select assignment `rx_shift[bit_number - 14'd1] <= majority` with a right shift that inserts `majority` at the most significant bit on each data-bit decision. Keep the existing data-bit decision timing and start-bit initialization so that after eight LSB-first decisions, `rx_shift` contains the same byte for the stop-bit decision. Preserve all other counter, parameter, reset, and output behavior; do not add a numeric top latency annotation.