# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| fir8 | done | 23 | 918,559 / 38,451 | 101 | 238 | ACCEPT 3, REJECT 3 | — |
| packet_fifo_build | done | 13 | 582,945 / 15,758 | 15 | 27 | ACCEPT 2, REJECT 1 | golden-model attempts 1 |
| skid_buffer_build | done | 8 | 294,444 / 7,275 | 15 | 11 | ACCEPT 1, REJECT 1 | golden-model attempts 1 |
| sync_fifo_build | done | 10 | 398,929 / 12,130 | 13 | 23 | ACCEPT 2 | golden-model attempts 1 |

## fir8: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 5 | 0 | 0 |
| evaluator.evaluate | 6 | 0 | 0 |
| generator.generate | 6 | 0 | 0 |
| planner.plan | 6 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 101 | 128 | -9.981 | yes |  |
| 1 | ACCEPT | True | 150 | 160 | -9.799 | yes |  |
| 2 | ACCEPT | True | 284 | 160 | -2.962 | yes |  |
| 3 | REJECT | True | 0 | 96 | -3.856 |  |  |
| 4 | ACCEPT | True | 238 | 51 | 0.807 | yes |  |
| 5 | REJECT | True | 279 | 196 | -0.341 |  |  |
| 6 | REJECT | True | 327 | 174 | -0.095 |  |  |

## packet_fifo_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 2 | 0 | 0 |
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 15 | 6 | -0.946 | yes |  |
| 1 | ACCEPT | True | 25 | 15 | -0.17 | yes |  |
| 2 | ACCEPT | True | 27 | 17 | 0.329 | yes |  |
| 3 | REJECT | True | 27 | 17 | 0.15 |  |  |

## skid_buffer_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 2 | 0 | 0 |
| generator.generate | 3 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 2 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 15 | 19 | 0.272 | yes |  |
| 1 | ACCEPT | True | 11 | 18 | 0.171 | yes |  |
| 2 | REJECT | True | 11 | 18 | 0.169 |  |  |

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
| 0 | BASELINE | True | 13 | 6 | -0.931 | yes |  |
| 1 | ACCEPT | True | 23 | 15 | 0.155 | yes |  |
| 2 | ACCEPT | True | 23 | 13 | 0.009 | yes |  |
