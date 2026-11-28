# PLAN — iteration 4
## Current state assessment
Iteration 2 is the verified incumbent at 3 LUTs and 4 FFs with feasible timing; iteration 3’s counter-sum rewrite was rejected because it tied those resource counts. The current seed uses a 3-bit binary stability counter and a registered `clean_reg`. The required top annotation is `// @latency 0`, and the frozen child cannot be edited.

## Hypothesis
A 3-bit maximal-length LFSR counter may reduce LUT use by replacing binary increment logic with shift/XOR logic while retaining the same four state bits.

## Instruction for generator
Keep `clean_reg` as the registered output and replace the binary `stability_count` progression with a 3-bit LFSR: use `000` as the matching/idle state, seed the first mismatching sample at `001`, and advance through `011, 111, 110, 101, 010, 100`. On a mismatch while in `100`, update `clean_reg` to `noisy` and return the state to `000`; when `noisy == clean_reg`, return the state to `000`. Preserve synchronous active-high reset, the update on the eighth consecutive mismatching sample, all ports, and `// @latency 0`; the expected LUT reduction is a hypothesis to verify against routed metrics.