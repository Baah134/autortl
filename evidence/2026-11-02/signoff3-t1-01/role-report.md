# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| counter8_build | done | 4 | 134,979 / 1,870 | 6 | 6 | REJECT 1 | — |
| debouncer_build | done | 16 | 613,464 / 17,922 | 4 | 3 | ACCEPT 2, REJECT 2 | generator repairs 1, golden-model attempts 1, planner spec attempts 1 |
| encoder8_build | done | 4 | 138,729 / 3,554 | 6 | 3 | ACCEPT 1 | — |
| pwm | done | 15 | 558,005 / 14,196 | 7 | 7 | REJECT 5 | — |

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
| generator.fix | 1 | 0 | 0 |
| generator.generate | 5 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.make_spec | 1 | 0 | 0 |
| planner.plan | 4 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 4 | 5 | 0.731 | yes |  |
| 1 | REJECT | True | 4 | 5 | 0.731 |  |  |
| 2 | ACCEPT | True | 3 | 5 | 0.731 | yes |  |
| 3 | REJECT | True | 4 | 5 | 0.731 |  |  |
| 4 | ACCEPT | True | 3 | 4 | 0.57 | yes |  |

## encoder8_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 1 | 0 | 0 |
| generator.generate | 2 | 0 | 0 |
| planner.plan | 1 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 6 | 4 | 0.528 | yes |  |
| 1 | ACCEPT | True | 3 | 4 | 0.591 | yes |  |

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
| 3 | REJECT | True | 9 | 9 | 0.46 |  |  |
| 4 | REJECT | True | 11 | 9 | 0.404 |  |  |
| 5 | REJECT | True | 11 | 9 | 0.404 |  |  |
