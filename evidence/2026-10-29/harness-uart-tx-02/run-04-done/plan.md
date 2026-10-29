# PLAN — iteration 3
## Current state assessment
Both prior iterations passed behavioral, verification, metric, and timing gates, but left the LUT count at 39, equal to the timing-feasible incumbent. The editable top is only a wrapper; its LUTs come from the frozen `uart_tx_core`, which must remain instantiated. There is no evidence that changing wrapper RTL can reduce LUTs, so any candidate must still prove a strict routed LUT reduction to be accepted.

## Hypothesis
Routing the child outputs through a packed intermediate wire may let Vivado collapse wrapper connectivity without changing the frozen core, though a LUT reduction is unlikely and must be measured.

## Instruction for generator
Keep the `uart_tx_core #( .DIV(868) )` instance and its clock, reset, data, and valid connections unchanged. Replace the direct `in_ready` and `tx` output connections with a two-bit intermediate wire, then continuously assign its bits to the existing top-level outputs. Preserve `// @latency 1` and all interface behavior; retain this candidate only if it passes every gate and routed LUT usage is strictly below 39.