# PLAN — iteration 4

## Current state assessment
The verified incumbent is timing-feasible at 614 LUTs and 262 FFs, so promotion requires a strict LUT reduction with FFs as the tie-breaker. Iteration 3 passed behavior and timing but was rejected at 1,329 LUTs; its shared-total round-output correction is already represented in the seed and should not be repeated. The seed’s own measurements are unknown, and the top’s numeric latency is unknown, so preserve its exact cycle behavior without adding a latency annotation requirement.

## Hypothesis
A factored 4-bit Shannon implementation of the shared AES S-box may reduce LUT use across its 20 byte lookups while preserving timing closure.

## Instruction for generator
In `aes_sbox_lookup`, replace the flat 256-entry `case(value)` with a two-level 4-bit decomposition: use `value[7:4]` to select a bank and `value[3:0]` to address that bank’s 16-entry truth table, sharing the bank-select logic across all eight output bits. Preserve the exact S-box mapping for all 256 inputs and leave the round, key schedule, controller, and top cycle behavior unchanged. Compare routed LUTs, setup WNS, and hold WHS against the 614-LUT incumbent; retain the candidate only if all gates pass and LUT count strictly decreases.