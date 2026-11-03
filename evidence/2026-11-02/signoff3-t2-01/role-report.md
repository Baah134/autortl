# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| fir8 | baseline_failed | 1 | 17,650 / 2,943 | — | — | — | generator repairs 1 |
| packet_fifo_build | done | 13 | 582,599 / 17,070 | 146 | 24 | ACCEPT 2, REJECT 1 | golden-model attempts 1 |
| skid_buffer_build | done | 8 | 303,646 / 7,414 | 12 | 11 | ACCEPT 2 | golden-model attempts 1 |
| sync_fifo_build | done | 11 | 437,910 / 13,957 | 13 | 23 | ACCEPT 2 | generator repairs 1, golden-model attempts 1 |

## fir8: baseline_failed
- error: Repair violated static/interface/latency contract

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| generator.fix | 1 | 0 | 0 |

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
| 0 | BASELINE | True | 146 | 96 | -1.796 | yes |  |
| 1 | ACCEPT | True | 107 | 102 | 0.007 | yes |  |
| 2 | ACCEPT | True | 24 | 42 | 0.107 | yes |  |
| 3 | REJECT | True | 27 | 15 | 0.312 |  |  |

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
| 1 | ACCEPT | True | 11 | 19 | 0.133 | yes |  |
| 2 | ACCEPT | True | 11 | 18 | 0.438 | yes |  |

## sync_fifo_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 2 | 0 | 0 |
| evaluator.evaluate | 2 | 0 | 0 |
| generator.fix | 1 | 0 | 0 |
| generator.generate | 3 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 2 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 13 | 6 | -0.931 | yes |  |
| 1 | ACCEPT | True | 23 | 15 | 0.105 | yes |  |
| 2 | ACCEPT | True | 23 | 13 | 0.153 | yes |  |
