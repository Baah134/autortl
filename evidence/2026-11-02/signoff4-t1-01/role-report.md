# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| counter8_build | done | 4 | 134,405 / 2,227 | 6 | 6 | REJECT 1 | — |
| debouncer_build | done | 16 | 596,347 / 18,293 | 4 | 2 | ACCEPT 1, REJECT 3 | golden-model attempts 1, planner spec attempts 2 |
| encoder8_build | done | 4 | 137,252 / 2,938 | 6 | 4 | ACCEPT 1 | — |
| pwm | done | 15 | 554,326 / 16,224 | 7 | 7 | REJECT 5 | — |

## counter8_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 1 | 0 | 0 |
| generator.generate | 2 | 0 | 0 |
| planner.plan | 1 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 6 | 8 | 0.424 | yes |  |
| 1 | REJECT | True | 6 | 8 | 0.554 |  |  |

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
| 0 | BASELINE | True | 4 | 5 | 0.731 | yes |  |
| 1 | REJECT | True | 4 | 5 | 0.731 |  |  |
| 2 | REJECT | True | 4 | 5 | 0.731 |  |  |
| 3 | ACCEPT | True | 2 | 8 | 0.591 | yes |  |
| 4 | REJECT | True | 2 | 8 | 0.591 |  |  |

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
| 2 | REJECT | True | 7 | 9 | 0.553 |  |  |
| 3 | REJECT | True | 48 | 33 | 0.464 |  |  |
| 4 | REJECT | True | 29 | 33 | 0.604 |  |  |
| 5 | REJECT | True | 13 | 33 | 0.597 |  |  |
