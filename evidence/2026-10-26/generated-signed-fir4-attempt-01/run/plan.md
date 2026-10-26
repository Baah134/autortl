# PLAN — iteration 3
## Current state assessment
The verified incumbent is timing-feasible at 80 LUTs, so this iteration must pass all fixed verification and routed-report gates, retain nonnegative setup and hold slack, and use strictly fewer than 80 LUTs to improve the objective. The current seed’s registered `full` backpressure calculation should remain intact: a trial that replaced it with a combinational ready chain failed setup timing, and a related ready-path surgery also remained timing-infeasible. The top must retain `// @latency 3` and all defined stream, reset, and cycle behavior.

## Hypothesis
Rewriting the constant-coefficient FIR arithmetic with explicitly sized signed shift/add/subtract expressions may reduce LUT use while leaving the critical ready path and pipeline timing unchanged.

## Instruction for generator
Keep the `full` register, `next_valid1/2/3` calculations, ready equations, slot movement, history updates, and reset logic unchanged. Replace only the `fir_value` constant multiplications and sum with signed, explicitly sized shift/add/subtract terms for coefficients 3, 5, 7, and 2, sign-extending each 8-bit sample/history value as needed and preserving the exact low 13-bit result. Preserve the latency annotation and registered outputs; the candidate qualifies only if the unchanged verification gates pass, routed setup and hold slack are nonnegative, and LUT count is below the incumbent’s 80.