# PLAN — iteration 3
## Current state assessment
The incumbent is timing-feasible at 95 LUTs and 254 FFs, with WNS 5.441 ns and WHS 0.134 ns, so iteration 3 needs a strict LUT reduction (or equal LUTs with fewer FFs) to improve the objective. Iterations 1 and 2 preserved behavior and timing but left resource counts unchanged; their address narrowing and payload-register reset restructuring should not be repeated unchanged. The top’s numeric latency is unknown, so no numeric top annotation is required.

## Hypothesis
Replacing the variable part-select in `axil_rd_if` with an explicit 8-way register-index case may let Vivado simplify constant and zero-valued register fields and reduce read-mux LUTs without changing registered read behavior.

## Instruction for generator
In `axil_rd_if`, replace `regs_flat[{araddr[4:2], 5'b0} +: 32]` with an explicit case on `araddr[4:2]` selecting the corresponding 32-bit slice, retaining the existing out-of-range handling for `araddr[5]`. Keep `rdata_reg`, `rresp_reg`, and `rvalid_reg` registered with the same reset, accept, stall, and transfer behavior; the read must still sample the pre-edge bank value. Preserve every top port and observable cycle, and do not add a top latency annotation because the authoritative top latency is unknown.