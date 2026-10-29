# PLAN — iteration 1

## Current state assessment

The incumbent is timing-feasible at WNS 0.494 ns and WHS 0.113 ns, with 55 LUTs, 37 FFs, no DSPs, and no BRAMs; the objective is strictly fewer LUTs. The dead `prev_count` is already absent from the measured FF count, and `count_next` is unlikely to need a register after synthesis. Top numeric latency is unknown, so no numeric annotation is required; preserve the existing cycle behavior and registered flags.

## Hypothesis

Replacing the explicit all-ones comparison and wraparound mux with natural fixed-width increment wrap plus a reduction-AND overflow test may reduce LUT use while preserving the counter’s outputs and timing feasibility.

## Instruction for generator

In the sequential `enable` branch, replace the `count_next` assignment and `count == {WIDTH{1'b1}}` conditional with `count <= count + 1'b1` and `overflow <= &count`; keep the existing `load` and `rst` priority and hold behavior. Remove the unused `prev_count` and `count_next` declarations and assignments. Preserve the registered threshold flags exactly, including sampling the pre-edge `count` on every non-reset edge. Keep the interface and parameters unchanged, add no numeric latency annotation, and require the fixed simulation and routed setup, hold, and metric-integrity gates before promotion.