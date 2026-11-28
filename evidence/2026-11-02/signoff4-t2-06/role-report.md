# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| fir8 | done | 21 | 830,403 / 37,992 | 101 | 275 | ACCEPT 3, REJECT 3 | — |
| packet_fifo_build | done | 13 | 581,859 / 20,044 | 15 | 26 | ACCEPT 1, REJECT 2 | golden-model attempts 1 |
| skid_buffer_build | done | 8 | 302,172 / 5,865 | 12 | 11 | ACCEPT 2 | golden-model attempts 1 |
| sync_fifo_build | done | 9 | 361,272 / 10,448 | 13 | 23 | ACCEPT 2 | golden-model attempts 1 |

## fir8: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 3 | 0 | 0 |
| evaluator.evaluate | 6 | 0 | 0 |
| generator.generate | 6 | 0 | 0 |
| planner.plan | 6 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 101 | 128 | -9.981 | yes |  |
| 1 | ACCEPT | True | 24 | 67 | -9.358 | yes |  |
| 2 | ACCEPT | True | 274 | 308 | 0.329 | yes |  |
| 3 | REJECT | True | 359 | 330 | -0.35 |  |  |
| 4 | REJECT | True | 274 | 308 | 0.329 |  |  |
| 5 | REJECT | True | 133 | 112 | 0.148 |  |  |
| 6 | ACCEPT | True | 275 | 308 | 0.571 | yes |  |

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
| 1 | ACCEPT | True | 26 | 30 | 0.331 | yes |  |
| 2 | REJECT | True | 26 | 30 | 0.323 |  |  |
| 3 | REJECT | True | 26 | 30 | 0.323 |  |  |

## skid_buffer_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 2 | 0 | 0 |
| generator.generate | 3 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 2 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 12 | 4 | -0.753 | yes |  |
| 1 | ACCEPT | True | 12 | 18 | 0.122 | yes |  |
| 2 | ACCEPT | True | 11 | 18 | 0.131 | yes |  |

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
| 1 | ACCEPT | True | 22 | 14 | -0.102 | yes |  |
| 2 | ACCEPT | True | 23 | 15 | 0.104 | yes |  |
