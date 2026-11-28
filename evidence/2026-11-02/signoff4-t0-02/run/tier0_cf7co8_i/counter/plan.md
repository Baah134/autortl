# PLAN — iteration 1

## Current state assessment

The incumbent is timing-feasible (routed WNS 0.494 ns, WHS 0.113 ns) at 55 LUTs and 37 FFs, so this `minimize_luts` run must strictly reduce LUTs to improve the objective. The seed has no known numeric top latency requirement; preserve its observed cycle behavior without adding a latency annotation. `prev_count` is dead state, and `count_next` plus the full-width all-ones comparison duplicate work in the enabled increment path.

## Hypothesis

Removing the unused `prev_count` and expressing wraparound through the natural `WIDTH`-bit increment result will preserve counter behavior while reducing LUT use, subject to routed measurement.

## Instruction for generator

Remove the unused `prev_count` declaration and all of its reset and update assignments. In the `enable` branch, use `count + 1'b1` at the `WIDTH`-bit count destination so overflow is detected from the pre-increment all-ones count while the count wraps naturally; remove the temporary `count_next` and its redundant assignment. Preserve reset-over-load-over-enable priority, overflow hold while disabled, overflow clear on load, and the registered flags’ one-cycle-old count semantics, including reset values and behavior for supported `WIDTH` and threshold parameters.