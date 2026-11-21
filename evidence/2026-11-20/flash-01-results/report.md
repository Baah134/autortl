# flash-01: Gemini 3.8 Flash, single call (40 tasks x 3 trials)

40 tasks, 120 graded cells. Intervals are 95% task-clustered bootstrap (10000 resamples, seed 20261115); trials of one task are not independent. Missing submissions count as failures; cells stopped by infrastructure (model quota, interruption) are not verdicts and are excluded from rates.

## Functional correctness (official testbench, upstream-compatible verdict)

| Arm | Pass | Rate | 95% CI | Always / never pass (tasks) | Missing | Excluded (infrastructure) |
|---|---|---|---|---|---|---|
| A single call | 110/120 | 91.7% | 83.3 to 98.3 | 35 / 2 | 5 | 0 |

## False acceptance (internally accepted, externally failing)

| Arm | Internally accepted | False acceptances | Rate | Cells |
|---|---|---|---|---|
| A single call | 0 | 0 | n/a | none |

Arm A submissions are never internally verified, so it has no accepted set.

## Cost

| Arm | Model calls | Calls per pass | Input tokens | Output tokens | Wall hours |
|---|---|---|---|---|---|
| A single call | 120 | 1.1 | 0 | 0 | 1.3 |

## By category (mean per-task pass rate)

| Category | Tasks | A single call |
|---|---|---|
| combinational_arithmetic | 3 | 100.0% |
| combinational_logic | 21 | 93.7% |
| fsm_control | 6 | 77.8% |
| sequential | 10 | 93.3% |

## Integrity

| Arm | Strict passes | Grader disagreements | Terminations |
|---|---|---|---|
| A single call | 110 | 0 | budget 5, done 115 |

Limits: public tasks do not exclude training contamination; one model and backend; functional correctness only, no area or timing claim; the single-call arm is one backend invocation, not a tools-enabled agent baseline.
