# PLAN — iteration 1

## Current state assessment

The incumbent is already timing-feasible on xc7a35tcpg236-1 at 10 ns: 6 LUTs, 4 FFs, WNS 0.528 ns, and WHS 0.009 ns; the fixed testbench passed. Since the objective is minimize_luts and the incumbent is feasible, promotion requires passing every gate and strictly reducing LUTs (or matching LUTs with fewer FFs). The top must retain `// @latency 1`, registered outputs, synchronous active-high reset behavior, and the exact priority result.

## Hypothesis

Replacing the serial priority chain with shared group-prefix Boolean equations may reduce LUT use below 6 while retaining the four required state bits and registered behavior.

## Instruction for generator

In `priority_encoder8_core`, replace the descending `if/else if` priority chain with explicit grouped reductions and Boolean equations for the three index bits, sharing upper-group priority prefixes where useful. Keep `valid` registered from `|request`, and keep index, valid, reset, and clock updates in the existing rising-edge behavior so outputs still change only after that edge. Preserve zero-request outputs and distinguish valid index 0 from invalid index 0; retain the top’s `// @latency 1` annotation and unchanged interface.