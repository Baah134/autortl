# PLAN — iteration 3

## Current state assessment

The incumbent is timing-feasible at 95 LUTs and 254 FFs, with WNS 5.441 ns and WHS 0.134 ns. Both prior read-mux rewrites were rejected: one increased LUTs to 136, and the other left LUT and FF counts unchanged. The current top’s numeric latency is unknown, so no numeric top annotation is required; its cycle behavior still must be preserved.

## Hypothesis

Factoring register-index decoding and byte strobes into shared write enables may reduce LUT use in the register-bank write logic while keeping the existing state and transfer timing.

## Instruction for generator

In `axil_regbank`, replace the nested `case (wr_idx)` and per-byte `if (wr_strb[b])` updates for `ctrl_reg`, `scratch_reg`, and `config_reg` with explicit shared enables per register and byte, formed from `wr_en`, the matching index, and `wr_strb[b]`. Use those enables to update only the selected byte from `wr_data`; retain the existing IRQ mask, IRQ status, status snapshot, and write-count behavior. Preserve synchronous reset and all observable cycles, and measure whether routed LUTs fall below 95 with FFs at or below 254.