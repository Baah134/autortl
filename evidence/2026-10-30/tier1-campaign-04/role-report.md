# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| counter8_build | done | 4 | 131,839 / 2,466 | 6 | 6 | REJECT 1 | — |
| debouncer_build | module_failed | 1 | 16,832 / 2,009 | — | — | — | planner spec attempts 1 |
| encoder8_build | done | 4 | 136,422 / 3,895 | 6 | 3 | ACCEPT 1 | — |
| pwm | done | 16 | 570,853 / 14,987 | 7 | 7 | REJECT 5 | generator repairs 1 |

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

## debouncer_build: module_failed
- error: example 0: input rst must be a masked port integer; example 0: input noisy must be a masked port integer; example 0: expected clean must be a masked port integer; example 1: input rst must be a masked port integer; example 1: input noisy must be a masked port integer; example 1: expected clean must be a masked port integer; example 2: input rst must be a masked port integer; example 2: input noisy must be a masked port integer; example 2: expected clean must be a masked port integer

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| planner.make_spec | 1 | 0 | 0 |

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
| generator.fix | 1 | 0 | 0 |
| generator.generate | 5 | 0 | 0 |
| planner.plan | 5 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 7 | 9 | 0.553 | yes |  |
| 1 | REJECT | True | 10 | 9 | 0.412 |  |  |
| 2 | REJECT | True | 7 | 9 | 0.553 |  |  |
| 3 | REJECT | True | 11 | 9 | 0.404 |  |  |
| 4 | REJECT | True | 10 | 9 | 0.404 |  |  |
| 5 | REJECT | True | 10 | 9 | 0.412 |  |  |
