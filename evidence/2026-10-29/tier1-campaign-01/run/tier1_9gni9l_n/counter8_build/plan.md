# PLAN — iteration 1

## Current state assessment

The 8-bit counter currently uses 6 LUTs and 8 FFs, with routed WNS 0.424 ns and WHS 0.226 ns; timing is feasible, so promotion requires a strict LUT reduction and all verification and metric gates to pass. The editable top is only a wrapper around a frozen counter module, and the measured baseline passes simulation, so preserve the synchronous active-high reset, enable hold behavior, modulo-256 wrap, registered output, and `// @latency 1`.

## Hypothesis

Inlining the counter into the editable top and expressing enable as the adder carry-in may let Vivado map the update with fewer LUTs while retaining the existing FFs and cycle behavior.

## Instruction for generator

Replace the child instance with an 8-bit registered counter in `counter8`, using a synchronous `if (rst) count_reg <= 8'd0; else count_reg <= count_reg + enable;` update and continuously drive `count` from that register. Retain the existing ports and `// @latency 1` annotation. The change is only a LUT-reduction candidate: promote it only if the frozen simulation and all deterministic checks pass, routed WNS and WHS remain nonnegative, metrics are valid, and LUT use is strictly below 6.