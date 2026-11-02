# PLAN — iteration 1

## Current state assessment

The incumbent passes simulation and timing, with 6 LUTs, 8 FFs, WNS 0.424 ns, and WHS 0.226 ns. Since timing is already feasible, promotion requires strictly fewer LUTs than the incumbent; equal LUT count with fewer FFs would also qualify, though all 8 output bits must retain registered state. The top requires `// @latency 1`.

## Hypothesis

Adding `enable` as the incrementer’s addend may reduce LUT use by replacing the register enable behavior with an enable-controlled carry input while preserving the counter’s cycle behavior.

## Instruction for generator

In `counter8_core`, replace the `else if (enable)` hold/update branch with an unconditional `count_reg <= count_reg + {7'b0, enable};` in the non-reset case, keeping synchronous active-high reset priority and the existing 8-bit state. Preserve the top interface, registered output, modulo-256 wraparound, and `// @latency 1` annotation. This is a LUT-reduction hypothesis, not an assumed gain: retain it only if the unchanged verification gates pass and routed LUT use is strictly below 6.