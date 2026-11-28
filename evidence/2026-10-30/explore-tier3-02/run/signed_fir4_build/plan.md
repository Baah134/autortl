# PLAN — iteration 3
## Current state assessment
Iteration 1 is the verified, timing-feasible incumbent at 80 LUTs and WNS 0.001 ns. Iteration 2 reduced usage to 51 LUTs but failed timing at WNS -0.024 ns; its violated path ends at `in_ready`. Since the incumbent already meets timing, iteration 3 must pass every verification and metric gate, close both setup and hold, and use fewer than 80 LUTs to qualify as an improvement.

## Hypothesis
Keep iteration 2’s narrow shift/add FIR arithmetic and register the three-slot full condition from the elastic pipeline’s exact next-state equations, which may remove the state-to-`in_ready` combinational path while keeping LUT usage below the incumbent.

## Instruction for generator
Replace the direct `in_ready` occupancy expression with `in_ready = !full || out_ready`, where `full` is a register maintained to equal `v1 && v2 && v3` after each rising edge. Compute its next value from the same stage-ready and old-valid transfer rules as the three slots, and clear it on synchronous reset; do not gate ready combinationally with reset. Keep the iteration 2 FIR shift/add arithmetic, `// @latency 3`, valid pipeline, accepted-sample history, registered outputs, and all handshake and reset behavior unchanged.