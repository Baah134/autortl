# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| fir8 | done | 22 | 873,522 / 33,017 | 101 | 133 | ACCEPT 5, REJECT 1 | — |
| packet_fifo_build | done | 12 | 539,157 / 15,290 | 24 | 23 | ACCEPT 3 | golden-model attempts 1 |
| skid_buffer_build | done | 8 | 303,475 / 6,365 | 12 | 11 | ACCEPT 2 | golden-model attempts 1 |
| sync_fifo_build | done | 10 | 402,259 / 12,830 | 144 | 25 | ACCEPT 2 | golden-model attempts 1 |

## fir8: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 4 | 0 | 0 |
| evaluator.evaluate | 6 | 0 | 0 |
| generator.generate | 6 | 0 | 0 |
| planner.plan | 6 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 101 | 128 | -9.981 | yes |  |
| 1 | ACCEPT | True | 150 | 160 | -9.799 | yes |  |
| 2 | ACCEPT | True | 300 | 160 | -2.049 | yes |  |
| 3 | ACCEPT | True | 351 | 160 | -0.294 | yes |  |
| 4 | REJECT | True | 410 | 160 | -2.814 |  |  |
| 5 | ACCEPT | True | 133 | 112 | 0.137 | yes |  |
| 6 | ACCEPT | True | 133 | 135 | 3.067 | yes |  |

## packet_fifo_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 1 | 0 | 0 |
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 24 | 10 | -0.93 | yes |  |
| 1 | ACCEPT | True | 31 | 15 | -0.386 | yes |  |
| 2 | ACCEPT | True | 29 | 16 | 0.089 | yes |  |
| 3 | ACCEPT | True | 23 | 14 | 0.135 | yes |  |

## skid_buffer_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 2 | 0 | 0 |
| generator.generate | 3 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 2 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 12 | 18 | -0.053 | yes |  |
| 1 | ACCEPT | True | 11 | 19 | 0.146 | yes |  |
| 2 | ACCEPT | True | 11 | 18 | 0.438 | yes |  |

## sync_fifo_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 2 | 0 | 0 |
| evaluator.evaluate | 2 | 0 | 0 |
| generator.generate | 3 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 2 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 144 | 96 | -1.736 | yes |  |
| 1 | ACCEPT | True | 13 | 6 | -0.931 | yes |  |
| 2 | ACCEPT | True | 25 | 16 | -0.449 | yes |  |
