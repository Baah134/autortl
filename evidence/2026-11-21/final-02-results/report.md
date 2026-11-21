# VerilogEval spec-to-RTL: single call vs AutoRTL (40 tasks x 3 trials)

40 tasks, 360 graded cells. Intervals are 95% task-clustered bootstrap (10000 resamples, seed 20261115); trials of one task are not independent. Missing submissions count as failures; cells stopped by infrastructure (model quota, interruption) are not verdicts and are excluded from rates.

## Functional correctness (official testbench, upstream-compatible verdict)

| Arm | Pass | Rate | 95% CI | Always / never pass (tasks) | Missing | Excluded (infrastructure) |
|---|---|---|---|---|---|---|
| A single call | 111/118 | 94.1% | 86.7 to 100.0 | 37 / 2 | 0 | 2 |
| B ablation | 100/118 | 84.7% | 74.2 to 93.3 | 31 / 4 | 8 | 2 |
| C full harness | 99/115 | 86.1% | 73.3 to 94.2 | 33 / 5 | 5 | 5 |

## Paired differences (same tasks; percentage points)

| Comparison | Mean difference | 95% CI | Tasks better / equal / worse |
|---|---|---|---|
| C full harness minus A single call | -9.2 | -19.2 to -0.8 | 1 / 34 / 5 |
| C full harness minus B ablation | +0.4 | -5.0 to +5.8 | 4 / 33 / 3 |
| B ablation minus A single call | -9.6 | -18.3 to -2.5 | 0 / 34 / 6 |

An interval that includes 0 does not show a difference.

## False acceptance (internally accepted, externally failing)

| Arm | Internally accepted | False acceptances | Rate | Cells |
|---|---|---|---|---|
| A single call | 0 | 0 | n/a | none |
| B ablation | 110 | 10 | 9.1% | Prob066_edgecapture#1, Prob070_ece241_2013_q2#1, Prob093_ece241_2014_q3#0, Prob093_ece241_2014_q3#1, Prob093_ece241_2014_q3#2, Prob139_2013_q2bfsm#0, Prob139_2013_q2bfsm#1, Prob149_ece241_2013_q4#0, Prob149_ece241_2013_q4#1, Prob149_ece241_2013_q4#2 |
| C full harness | 110 | 11 | 10.0% | Prob027_fadd#2, Prob066_edgecapture#0, Prob066_edgecapture#1, Prob066_edgecapture#2, Prob093_ece241_2014_q3#0, Prob093_ece241_2014_q3#1, Prob093_ece241_2014_q3#2, Prob139_2013_q2bfsm#0, Prob139_2013_q2bfsm#1, Prob149_ece241_2013_q4#0, Prob149_ece241_2013_q4#2 |

Arm A submissions are never internally verified, so it has no accepted set.

## Cost

| Arm | Model calls | Calls per pass | Input tokens | Output tokens | Wall hours |
|---|---|---|---|---|---|
| A single call | 120 | 1.1 | 1,340,327 | 17,674 | 0.2 |
| B ablation | 812 | 8.1 | 19,881,590 | 368,453 | 10.6 |
| C full harness | 792 | 8.0 | 19,516,749 | 354,596 | 10.7 |

## By category (mean per-task pass rate)

| Category | Tasks | A single call | B ablation | C full harness |
|---|---|---|---|---|
| combinational_arithmetic | 3 | 100.0% | 100.0% | 88.9% |
| combinational_logic | 21 | 95.2% | 88.1% | 90.5% |
| fsm_control | 6 | 83.3% | 72.2% | 66.7% |
| sequential | 10 | 96.7% | 80.0% | 83.3% |

## Integrity

| Arm | Strict passes | Grader disagreements | Terminations |
|---|---|---|---|
| A single call | 111 | 0 | done 118, model_blocked 2 |
| B ablation | 100 | 0 | done 110, failed 8, interrupted 2 |
| C full harness | 99 | 0 | done 110, failed 5, interrupted 5 |

Limits: public tasks do not exclude training contamination; one model and backend; functional correctness only, no area or timing claim; the single-call arm is one backend invocation, not a tools-enabled agent baseline.
