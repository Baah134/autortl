# PLAN — iteration 3

## Current state assessment

The incumbent is timing-feasible at 25 LUTs, 36 FFs, WNS 0.343 ns, and WHS 0.14 ns. Iterations 1 and 2 both passed verification and timing but were rejected because LUT use stayed at 25; iteration 2’s `keep_hierarchy` attribute did not improve it. The editable top is only a wrapper around the frozen core, which must remain live, so the top-level RTL offers no evident behavior-preserving way to reduce the core’s LUT count.

## Hypothesis

No top-only RTL change has a credible, falsifiable path to fewer LUTs while preserving the required live core instance and exact behavior; another wrapper-only rewrite is unlikely to beat the feasible incumbent.

## Instruction for generator

Keep the unconditional `spi_master_core #(.HALF_PERIOD(2)) u_spi_master_core` instance and its direct port connections, with `// @latency 33`; do not repeat the `keep_hierarchy` proposal from iteration 2. The core is frozen and already accounts for the measured implementation, so avoid adding output logic, which risks increasing LUTs or changing behavior without a plausible reduction. If no measurable LUT reduction is available within this boundary, retain the baseline and report no accepted improvement.