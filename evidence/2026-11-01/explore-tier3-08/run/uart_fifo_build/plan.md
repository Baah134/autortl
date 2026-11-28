# PLAN — iteration 5
## Current state assessment
Iteration 4 is the verified incumbent at 36 LUTs and 27 FFs, with setup WNS 0.179 ns and hold passing. The seed already uses narrowed FIFO occupancy and pointer registers, a UART shift register, and a parameter-sized bit counter, so those changes should not be repeated. The top’s numeric latency is unknown, so no numeric top annotation is required.

## Hypothesis
Replacing the FIFO occupancy counter with read/write wrap flags should remove its increment/decrement logic and reduce FF use from 10 FIFO tracking bits to 8, with LUT count expected to stay level or fall.

## Instruction for generator
In `byte_fifo`, replace `occupancy` with one wrap flag per read/write pointer, toggled when its pointer wraps at `DEPTH-1`; define empty from equal pointers with equal flags and full from equal pointers with different flags. Derive `out_valid`, `in_ready`, and the empty `out_data` value from those conditions, while preserving the existing enqueue/dequeue handshakes, ordering, reset, and pointer behavior for supported `DEPTH` values. Keep `uart_tx` and the top interface and cycle behavior unchanged.