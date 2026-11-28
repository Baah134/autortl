# PLAN — iteration 2

## Current state assessment
The incumbent is timing-feasible at 42 LUTs, 90 FFs, WNS 0.554 ns, and WHS 0.063 ns. Iteration 1 passed verification and timing but was rejected: it kept LUTs at 42 and increased FFs to 93. Promotion now requires fewer than 42 LUTs, or 42 LUTs with fewer than 90 FFs. The top’s numeric latency is unknown, so no numeric top annotation is required.

## Hypothesis
Computing the arbiter winner as a one-hot mask and reusing it for grant and write-data selection may reduce LUT use by sharing selection logic.

## Instruction for generator
In `rr_arbiter4`, replace the binary `winner` plus `case (winner)` input mux with a combinational one-hot winner mask, and use that mask for the registered grant and OR-of-masked `addrN`/`dataN` selection. Preserve the round-robin priority for every `last` value, hold `last` on idle, and keep synchronous reset, registered outputs, and zero write fields on idle/reset unchanged. This is a new logic change; do not repeat iteration 1’s removal of the registered `wr_en` state.