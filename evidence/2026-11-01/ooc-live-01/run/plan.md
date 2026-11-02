# PLAN — iteration 1

## Current state assessment

The verified incumbent is timing-feasible at 137 LUTs, 254 FFs, WNS 5.779 ns, and WHS 0.109 ns; the objective is to reduce LUTs while preserving timing closure and all behavior. The current top latency is unknown, so a numeric top annotation is not required. The routed critical path excerpt shows one logic level and is mostly routing delay; I/O paths are unconstrained in this out-of-context flow.

## Hypothesis

Inlining the register-bank state into the editable top and expressing the three byte-strobed registers as per-byte enabled writes may let Vivado use flip-flop clock enables and reduce LUTs without adding FFs or changing cycles.

## Instruction for generator

Keep `axil_wr_if` and `axil_rd_if` as the write and read interfaces, but replace the `axil_regbank` instance with equivalent bank state and logic inside `axil_regs`. For `ctrl_q`, `scratch_q`, and `config_q`, replace the 32-bit merged-data expressions with four independently enabled byte assignments selected by `wr_en`, `wr_idx`, and the matching `wr_strb` bit; preserve all reset values, write-count behavior, W1C set priority, status sampling, read mapping, and `ctrl`/`irq` outputs. This should reduce LUT use if byte enables map to FF clock enables; compare routed LUTs and FFs against 137/254 and require simulation plus setup and hold closure before promotion.