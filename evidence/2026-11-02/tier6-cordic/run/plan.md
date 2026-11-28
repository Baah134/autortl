# PLAN — iteration 4
## Current state assessment
The accepted incumbent is timing-feasible at 194 LUTs and 95 FFs, with WNS 0.076 ns and WHS 0.096 ns. Iterations 2 and 3 passed behavior and timing but increased LUTs, so they did not improve the objective. The seed has a separate `in_ready_reg`, although the contract defines readiness as `!busy && !out_valid`; the top’s numeric latency is unknown, so no numeric annotation is required.

## Hypothesis
Deriving `in_ready` directly from the existing state registers should remove redundant state and may reduce LUTs while preserving the handshake and registered result outputs.

## Instruction for generator
In `cordic_engine`, remove `in_ready_reg` and its reset and branch assignments, and drive `in_ready` as `!busy_reg && !out_valid_reg`. Keep the registered cosine and sine outputs and their update behavior unchanged to preserve output timing; do not repeat the rejected arithmetic or rounding rewrites from iterations 2 and 3. Preserve synchronous reset behavior and verify readiness across acceptance, all 16 busy edges, output stalls, transfers, and reset.