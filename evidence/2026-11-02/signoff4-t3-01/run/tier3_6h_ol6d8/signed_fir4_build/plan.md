# PLAN — iteration 3
## Current state assessment
Iteration 1 is the verified, timing-feasible incumbent at 81 LUTs, 67 FFs, WNS 0.333 ns, and WHS 0.103 ns. Iteration 2 passed behavioral and timing gates but was rejected because it used 82 LUTs; its arithmetic-width change should not be repeated. The generation seed includes the registered full-occupancy flag that supports timing closure, so preserve that ready path.

## Hypothesis
Reassociating the four existing signed 13-bit FIR terms into two balanced pairs may map to fewer LUTs while preserving timing closure, which is testable against the incumbent’s 81 LUTs.

## Instruction for generator
In `signed_fir4_core`, keep the existing signed 13-bit `term0` through `term3`, but replace the serial `term0 + term1 + term2 + term3` expression with two signed 13-bit pair sums, `(term0 + term1)` and `(term2 + term3)`, followed by their sum. This is a distinct arithmetic reassociation from iteration 2’s term-width changes; preserve signed 13-bit result behavior and verify extrema. Leave the three elastic data/valid stages, registered full-occupancy ready logic, accepted-sample history updates, synchronous reset behavior, and top `// @latency 3` unchanged.