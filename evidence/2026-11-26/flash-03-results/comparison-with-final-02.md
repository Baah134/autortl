# Single call: Gemini 3.8 Flash-low (closed-book) vs Codex, 40 VerilogEval tasks

One arm from each of two separately graded attempts on the same 40 tasks (Codex single call (final-02): arm `single_call`; Flash-low single call (flash-03): arm `single_call`), paired by task. Intervals are 95% task-clustered bootstrap (10000 resamples, seed 20261115). Missing submissions count as failures; cells stopped by infrastructure (model quota, interruption) are not verdicts and are excluded from rates.

## Functional correctness (official testbench, upstream-compatible verdict)

| Run | Arm | Pass | Rate | 95% CI | Always / never pass (tasks) | Missing | Excluded (infrastructure) | Model calls | Calls per pass |
|---|---|---|---|---|---|---|---|---|---|
| Codex single call (final-02) | single_call | 111/118 | 94.1% | 86.7 to 100.0 | 37 / 2 | 0 | 2 | 120 | 1.1 |
| Flash-low single call (flash-03) | single_call | 103/120 | 85.8% | 75.8 to 94.2 | 32 / 1 | 0 | 0 | 120 | 1.2 |

## Paired difference (tasks with a verdict in both runs; percentage points)

| Comparison | Tasks compared | Mean difference | 95% CI | Tasks better / equal / worse |
|---|---|---|---|---|
| Flash-low single call (flash-03) minus Codex single call (final-02) | 40 | -8.3 | -15.8 to -1.7 | 1 / 33 / 6 |

An interval that includes 0 does not show a difference.

## Tasks where the runs differ

| Task | Codex single call (final-02) | Flash-low single call (flash-03) | Difference (points) |
|---|---|---|---|
| Prob057_kmap2 | 100.0% | 33.3% | -66.7 |
| Prob066_edgecapture | 100.0% | 33.3% | -66.7 |
| Prob070_ece241_2013_q2 | 100.0% | 33.3% | -66.7 |
| Prob078_dualedge | 66.7% | 33.3% | -33.3 |
| Prob137_fsm_serial | 100.0% | 33.3% | -66.7 |
| Prob139_2013_q2bfsm | 100.0% | 33.3% | -66.7 |
| Prob149_ece241_2013_q4 | 0.0% | 33.3% | +33.3 |

Limits: the two runs were registered and run separately and may use different models, backends and dates, so a difference is not attributable to a single factor; public tasks do not exclude training contamination; functional correctness only, no area or timing claim.
