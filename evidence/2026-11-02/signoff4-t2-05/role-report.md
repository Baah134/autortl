# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| fir8 | done | 20 | 786,528 / 33,761 | 101 | 285 | ACCEPT 1, REJECT 5 | — |
| packet_fifo_build | done | 12 | 541,575 / 15,863 | 146 | 27 | ACCEPT 3 | golden-model attempts 1 |
| skid_buffer_build | done | 9 | 333,443 / 8,333 | 15 | 11 | ACCEPT 2 | golden-model attempts 1 |
| sync_fifo_build | done | 9 | 360,448 / 9,430 | 13 | 21 | ACCEPT 2 | golden-model attempts 1 |

## fir8: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 2 | 0 | 0 |
| evaluator.evaluate | 6 | 0 | 0 |
| generator.generate | 6 | 0 | 0 |
| planner.plan | 6 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 101 | 128 | -9.981 | yes |  |
| 1 | ACCEPT | True | 285 | 259 | 1.387 | yes |  |
| 2 | REJECT | True | 133 | 112 | 0.148 |  |  |
| 3 | REJECT | True | 229 | 332 | 1.305 |  |  |
| 4 | REJECT | True | 133 | 112 | 0.148 |  |  |
| 5 | REJECT | True | 64 | 128 | -5.32 |  |  |
| 6 | REJECT | True | 285 | 259 | 1.387 |  |  |

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
| 0 | BASELINE | True | 146 | 96 | -1.796 | yes |  |
| 1 | ACCEPT | True | 18 | 8 | -0.915 | yes |  |
| 2 | ACCEPT | True | 29 | 17 | 0.142 | yes |  |
| 3 | ACCEPT | True | 27 | 17 | 0.17 | yes |  |

## skid_buffer_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 1 | 0 | 0 |
| evaluator.evaluate | 2 | 0 | 0 |
| generator.generate | 3 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 2 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 15 | 19 | 0.302 | yes |  |
| 1 | ACCEPT | True | 14 | 19 | 0.088 | yes |  |
| 2 | ACCEPT | True | 11 | 18 | 0.438 | yes |  |

## sync_fifo_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 1 | 0 | 0 |
| evaluator.evaluate | 2 | 0 | 0 |
| generator.generate | 3 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 2 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 13 | 6 | -0.931 | yes |  |
| 1 | ACCEPT | True | 21 | 26 | -0.273 | yes |  |
| 2 | ACCEPT | True | 21 | 27 | 0.004 | yes |  |
