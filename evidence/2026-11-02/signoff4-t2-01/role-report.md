# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| fir8 | done | 20 | 784,207 / 32,477 | 101 | 288 | ACCEPT 3, REJECT 3 | — |
| packet_fifo_build | done | 13 | 584,422 / 20,148 | 15 | 23 | ACCEPT 2, REJECT 1 | golden-model attempts 1 |
| skid_buffer_build | done | 9 | 343,585 / 8,974 | 12 | 12 | ACCEPT 2 | golden-model attempts 1 |
| sync_fifo_build | done | 8 | 301,181 / 9,011 | 13 | 21 | ACCEPT 1, REJECT 1 | golden-model attempts 1 |

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
| 1 | ACCEPT | True | 133 | 112 | 0.148 | yes |  |
| 2 | REJECT | True | 133 | 112 | 0.148 |  |  |
| 3 | REJECT | True | 64 | 128 | -5.307 |  |  |
| 4 | REJECT | True | 133 | 112 | 0.148 |  |  |
| 5 | ACCEPT | True | 202 | 208 | 1.431 | yes |  |
| 6 | ACCEPT | True | 288 | 259 | 1.938 | yes |  |

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
| 1 | ACCEPT | True | 21 | 15 | -0.087 | yes |  |
| 2 | ACCEPT | True | 23 | 17 | 0.306 | yes |  |
| 3 | REJECT | True | 35 | 30 | 0.174 |  |  |

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
| 0 | BASELINE | True | 12 | 4 | -0.753 | yes |  |
| 1 | ACCEPT | True | 8 | 18 | -0.193 | yes |  |
| 2 | ACCEPT | True | 12 | 18 | 0.009 | yes |  |

## sync_fifo_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 1 | 0 | 0 |
| evaluator.evaluate | 1 | 0 | 0 |
| generator.generate | 3 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 2 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 13 | 6 | -0.931 | yes |  |
| 1 | ACCEPT | True | 21 | 27 | 0.153 | yes |  |
| 2 | REJECT | False | None | None | None |  |  |
