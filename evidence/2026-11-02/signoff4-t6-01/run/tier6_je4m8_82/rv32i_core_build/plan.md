# PLAN — iteration 4
## Current state assessment
The verified incumbent is timing-feasible at 1,992 LUTs, 4,357 FFs, and 0.526 ns WNS; iteration 3 was accepted as a strict LUT improvement. The generation seed already combines ALU add/subtract, shifts, and comparisons, so those changes should not be repeated. The current top’s numeric latency is unknown, so no numeric top annotation is required; preserve its exact cycle behavior and pass every deterministic verification and routed-report gate.

## Hypothesis
Explicitly sharing immediate-format selection and sign extension in `rv_decode` may reduce LUT usage while preserving the decoder’s outputs for every opcode.

## Instruction for generator
In `rv_decode`, replace the opcode `case` branches’ separate assignments to `imm` with shared I, S, B, U, and J immediate wires and a single opcode-class selection for `imm`; keep the existing opcode-specific assignments for `kind`, `a_sel`, `b_sel`, and `alu_op`. Reuse the I-format value for OP-IMM, JALR, and LOAD, and preserve every immediate’s bit positions and sign extension exactly. Retain the top interface and cycle behavior, then compare routed LUTs against the 1,992-LUT feasible incumbent; accept an objective improvement only if all gates pass and LUT usage strictly decreases (or ties with fewer FFs).