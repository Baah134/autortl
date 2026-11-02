# PLAN — iteration 3

## Current state assessment
The incumbent uses 16 LUTs and is timing-feasible at WNS 0.445 ns and WHS 0.208 ns. Iterations 1 and 2 both passed the reported verification and timing gates but were rejected because LUT usage stayed at 16; the direct CRC equations and shared CRC/output register approaches have already been tried.

## Hypothesis
Factoring shared XOR terms in the CRC linear transform together with the frame-end state update may let Vivado map the CRC and seed selection into fewer LUTs while preserving the one-byte-per-cycle behavior.

## Instruction for generator
In `crc16_stream_core`, keep distinct frame-state and output registers, but replace the current CRC loop with a factored XOR network that shares intermediate terms between the CRC result and the next frame state, including the `in_last` seed selection. This differs from the previously tried standalone output equations and shared-register design; aim for fewer than 16 LUTs and retain the existing register count where needed. Preserve the exact CRC-16/CCITT-FALSE mapping, acceptance and replacement behavior, registered outputs, stall stability, and synchronous reset semantics; retain `// @latency 1` on the top.