# PLAN — iteration 6

## Current state assessment

The verified incumbent is timing-feasible at 301 LUTs and 367 FFs. Iterations 4 and 5 passed behavior and timing but were rejected because they used 304 and 302 LUTs, respectively; their coefficient-width changes did not improve the LUT objective. The current seed retains the accepted five-stage datapath and `// @latency 5`. Timing and promotion still require simulation, valid routed metrics, WNS ≥ 0 and WHS ≥ 0; the objective requires fewer than 301 LUTs, or equal LUTs with fewer FFs.

## Hypothesis

Narrowing the stage-four rounding adder to the exact 28-bit accumulator width and taking the 17-bit shifted result directly may reduce LUTs while preserving rounding and saturation behavior.

## Instruction for generator

In `fir16_sym_core`, change only the `rounded_in` rounding pattern: perform `acc_full + 28'sd1024` as a signed 28-bit operation, then assign bits `[27:11]` to the existing signed 17-bit `rounded4` register. The contract bounds the accumulator and biased value within signed 28-bit range, and this slice preserves the arithmetic right-shift result used by saturation. Keep the five elastic slots, register enables, reset behavior, top interface, and `// @latency 5` unchanged.