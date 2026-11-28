# PLAN — iteration 2
## Current state assessment
The incumbent is timing-feasible at 42 LUTs, with WNS 0.554 ns and WHS 0.063 ns. Iteration 1 passed behavioral and timing gates but used 50 LUTs after replacing the arbiter’s priority chains and binary winner path with explicit one-hot winner logic; it did not improve the LUT objective. The top’s numeric latency is unknown, so no numeric top annotation is required.

## Hypothesis
Representing the arbiter’s saved priority position as a four-bit one-hot state may reduce priority-selection logic enough to bring routed LUT use below 42, at the cost of two additional FFs.

## Instruction for generator
Change only `rr_arbiter4`’s binary `last` state and its dependent priority-selection logic: keep a four-bit one-hot pointer, reset it to requester 3, and derive the winner using parallel Boolean conditions from the pointer and `req`. Advance the pointer only when a requester wins; preserve the registered grant, write enable, address, and data behavior, including zero outputs on idle and synchronous reset. Do not repeat iteration 1’s explicit one-hot winner implementation with binary `last`; the proposed change is the priority state representation. Preserve `regfile8x8` and the top interface, and judge the candidate on unchanged simulation and routed gates, requiring strictly fewer than 42 LUTs while retaining setup and hold closure.