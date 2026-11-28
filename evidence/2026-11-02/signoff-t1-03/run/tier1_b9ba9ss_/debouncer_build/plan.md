# PLAN — iteration 4
## Current state assessment
The verified incumbent is already timing-feasible at 3 LUTs and 4 FFs, so promotion requires a strict improvement in the `(LUTs, FFs)` objective while passing every behavior, simulation, timing, and metric gate. Iterations 1–3 tried LFSR, down-counter, and up-counter variants with unchanged resource counts; the current source is only a transparent wrapper around the frozen child, so inlining alone is not an optimization.

## Hypothesis
A 3-bit Johnson sequence counter may implement the eight-cycle qualification with simpler next-state and terminal decoding logic, potentially reducing LUT use while preserving the existing three counter FFs and registered `clean`.

## Instruction for generator
Replace the child instance in `debouncer_top` with inline logic that keeps a registered `clean` and a 3-bit Johnson counter, using the sequence `000, 001, 011, 111, 110, 100, 000` with explicit phase handling so `clean` updates on the eighth consecutive mismatch cycle. Synchronously reset both registers to zero; clear the counter whenever `noisy == clean`, and preserve `clean` otherwise. Include `// @latency 0`; retain the exact ports and cycle behavior, and do not modify the frozen child.