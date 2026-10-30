# PLAN — iteration 2
## Current state assessment
The incumbent is timing-feasible at 41 LUTs, 90 FFs, WNS 0.554 ns and WHS 0.098 ns. Iteration 1’s top-level arbiter rewrite passed verification but kept the same LUT count, so it did not meet the strict LUT-reduction objective. The top latency is unknown; no numeric annotation is required.

## Hypothesis
Keeping the frozen arbiter and changing the register-file read selection to a shared one-hot decode with a balanced masked-OR tree may reduce LUT use while preserving timing closure.

## Instruction for generator
Keep the `rr_arbiter4` instance and its connections; replace only the `regfile8x8` instance with equivalent top-level storage logic. Decode `rd_addr` once into eight one-hot selects, mask each stored byte, and combine the terms in a balanced OR tree feeding a registered `rd_data` that preserves read-before-write behavior. Preserve synchronous active-high reset of every entry and `rd_data`, write blocking during reset, and the existing registered arbiter-to-memory write timing.