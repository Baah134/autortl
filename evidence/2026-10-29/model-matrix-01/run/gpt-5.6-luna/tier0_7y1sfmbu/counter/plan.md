# PLAN — iteration 1
## Current state assessment

The verified incumbent passes simulation and routed setup/hold timing on xc7a35tcpg236-1: 55 LUTs, 37 FFs, WNS 0.494 ns, and WHS 0.113 ns. The seed contains full-width zero/all-ones comparisons, unused state, and a redundant temporary, but its exact observable behavior must remain unchanged. Current-top latency is UNKNOWN because `declared_latency.known=false`; no numeric `// @latency` annotation is required, and its absence must not block acceptance.

## Hypothesis

Replacing full-width equality tests with reduction operators will reduce routed LUT usage below 55 without adding registers, latency, or timing risk.

## Instruction for generator

In the editable `counter` module, replace the `count == {WIDTH{1'b0}}` test used for `at_zero` with `~(|count)`, and replace the all-ones wrap test `count == {WIDTH{1'b1}}` with `&count`. Preserve the existing registered outputs, synchronous reset, reset > load > enable priority, overflow hold behavior, threshold comparisons, and pre-update flag semantics; do not add or remove pipeline stages or add a numeric latency annotation. Validate high-bit values, wraparound, disabled/load cycles, reset behavior, and all supported `WIDTH` and threshold parameter values.