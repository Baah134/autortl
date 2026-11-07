# PLAN — iteration 6
## Current state assessment
The verified incumbent is timing-feasible at 1.387 ns register-to-register WNS, so a candidate must close timing and strictly exceed that value to replace it. Iterations 3–5 did not improve the incumbent; iteration 5’s symmetric-tap approach still missed setup, and its trial path reached 12 logic levels. The seed retains separate product wires and registered `acc1`–`acc7` stages. The baseline’s reported critical path cascaded through five DSP48E1s before a carry chain, suggesting DSP mapping of the accumulation is a timing risk.

## Hypothesis
Keep the multiplier products and all state registers, but force the 32-bit `pN + acc` accumulation additions into fabric carry chains so Vivado cannot combine the registered accumulation stages into a long DSP48 cascade; this may shorten the critical path at modest LUT cost.

## Instruction for generator
In `fir8`, retain `x_d`, `p0`–`p7`, `acc1`–`acc7`, `y_out`, the sequential reset and update structure, and `// @latency 1`. Isolate each existing 32-bit accumulation expression (`p6 + acc7` through `p1 + acc2`, and `p0 + acc1`) as a signed 32-bit sum wire with `(* use_dsp = "no" *)`, then register that sum into the same destination on the same edge; leave `acc7 <= p7` unchanged. Preserve the full 32-bit wraparound and verify that the mapped path no longer cascades through multiple DSP48E1s, while checking simulation, routed setup and hold, and reg-to-reg WNS against the 1.387 ns incumbent.