# PLAN — iteration 2
## Current state assessment
Iteration 1 is the verified timing-feasible best at 1530 LUTs and 3325 FFs, with WNS 0.916 ns; its register-file reset-to-valid-bit change was accepted. The objective is now strict LUT reduction while retaining setup and hold closure. The current top’s numeric latency is unknown, so no numeric top annotation is required; its observable cycles and all memory read, write, and reset behavior remain fixed.

## Hypothesis
Applying reset validity bits to the instruction and data memories can remove reset logic from their wide storage arrays, reduce LUT use, and may improve RAM inference, at the cost of validity FFs and read masking.

## Instruction for generator
In `rv_imem` and `rv_dmem`, remove the reset loops that clear the data arrays and add per-word valid bits that reset to zero; leave the wide arrays unreset. On reads, register zero for an invalid address and otherwise register the addressed word, using pre-edge validity so same-edge reads and writes remain read-first; on writes, update the addressed word and set its valid bit. Keep each registered output’s synchronous reset-to-zero behavior, ignore writes during reset, and preserve the existing address, latency, and top-level cycle behavior.