# PLAN — iteration 1

## Current state assessment

The incumbent is timing-feasible at 6 LUTs, 8 FFs, WNS 0.424 ns, and WHS 0.226 ns; the objective is strictly fewer LUTs, or equal LUTs with fewer FFs. No prior iteration results are available. Preserve the 8-bit modulo count, synchronous active-high reset priority, enable hold behavior, registered output, and top `// @latency 1`; promotion still requires the frozen testbench, all compile and simulation gates, valid routed metrics, and nonnegative setup and hold slack.

## Hypothesis

Adding the one-bit enable as the increment operand may let Vivado absorb enable into the carry chain and reduce LUT use while retaining the same 8 FFs and cycle behavior.

## Instruction for generator

In `counter8_core`, replace the `else if (enable)` increment with an unconditional enabled addition in the non-reset branch, using `count_reg + {7'b0, enable}` so a low enable adds zero and holds the value. Keep the synchronous reset branch first and preserve the registered 8-bit output; retain `// @latency 1` on `counter8`. Compare routed LUTs against the incumbent and keep the candidate only if it passes every gate and strictly improves the LUT objective.