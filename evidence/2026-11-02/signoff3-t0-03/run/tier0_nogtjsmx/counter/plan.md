# PLAN — iteration 1
## Current state assessment
The verified incumbent is timing-feasible at 55 LUTs and 37 FFs, with WNS 0.494 ns and WHS 0.113 ns; the objective is to reduce LUTs while preserving timing closure. The current top’s numeric latency is unknown, and the fixed testbench checks registered flags, reset priority, overflow hold, and counter wrap behavior.

## Hypothesis
Removing the redundant all-ones mux from the count update may reduce LUT use while the natural modulo-`WIDTH` increment still wraps the count to zero.

## Instruction for generator
In the sequential counter update, replace the explicit `count == {WIDTH{1'b1}}` branch that selects zero versus `count_next` with an unconditional `count <= count + 1'b1` on enabled increments. Preserve overflow’s existing enabled-cycle all-ones detection, load clearing, disabled hold, synchronous reset, and reset-over-load-over-enable priority. Keep all registered threshold flags computed from the pre-edge count, with their current reset values and cycle behavior. Do not add a numeric latency annotation; accept only if the fixed checks pass and routed LUT count is strictly lower than the incumbent while setup and hold slack remain nonnegative.