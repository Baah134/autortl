# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| counter8_build | done | 4 | 133,886 / 1,979 | 6 | 6 | REJECT 1 | — |
| debouncer_build | done | 16 | 589,778 / 15,066 | 3 | 2 | ACCEPT 1, REJECT 3 | golden-model attempts 1, planner spec attempts 2 |
| encoder8_build | done | 4 | 137,864 / 2,848 | 6 | 4 | ACCEPT 1 | — |
| pwm | done | 15 | 552,018 / 14,299 | 7 | 7 | REJECT 5 | — |

## counter8_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 1 | 0 | 0 |
| generator.generate | 2 | 0 | 0 |
| planner.plan | 1 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 6 | 8 | 0.424 | yes |  |
| 1 | REJECT | True | 6 | 8 | 0.555 |  |  |

## debouncer_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 4 | 0 | 0 |
| generator.generate | 5 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.make_spec | 2 | 0 | 0 |
| planner.plan | 4 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 3 | 4 | 0.57 | yes |  |
| 1 | REJECT | True | 3 | 4 | 0.557 |  |  |
| 2 | REJECT | True | 3 | 4 | 0.558 |  |  |
| 3 | REJECT | True | 3 | 4 | 0.57 |  |  |
| 4 | ACCEPT | True | 2 | 8 | 0.579 | yes |  |

## encoder8_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 1 | 0 | 0 |
| generator.generate | 2 | 0 | 0 |
| planner.plan | 1 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 6 | 4 | 0.528 | yes |  |
| 1 | ACCEPT | True | 4 | 4 | 0.591 | yes |  |

## pwm: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 5 | 0 | 0 |
| generator.generate | 5 | 0 | 0 |
| planner.plan | 5 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 7 | 9 | 0.553 | yes |  |
| 1 | REJECT | True | 10 | 9 | 0.412 |  |  |
| 2 | REJECT | True | 10 | 9 | 0.463 |  |  |
| 3 | REJECT | True | 11 | 9 | 0.404 |  |  |
| 4 | REJECT | True | 10 | 9 | 0.404 |  |  |
| 5 | REJECT | True | 8 | 9 | 0.594 |  |  |
