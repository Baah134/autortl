# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| axil_regs_build | done | 15 | 669,130 / 19,230 | 95 | 95 | REJECT 3 | golden-model attempts 3 |
| fir16_sym_build | done | 26 | 1,248,485 / 52,451 | 307 | 78 | ACCEPT 4, REJECT 4 | golden-model attempts 1 |
| uart_rx_fifo_build | done | 16 | 670,646 / 25,398 | 70 | 59 | ACCEPT 2, REJECT 1 | golden-model attempts 3 |

## axil_regs_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 6 | 0 | 0 |
| generator.golden_model | 3 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 95 | 254 | 5.441 | yes |  |
| 1 | REJECT | True | 95 | 254 | 5.441 |  |  |
| 2 | REJECT | True | 95 | 254 | 5.441 |  |  |
| 3 | REJECT | True | 95 | 254 | 5.441 |  |  |

## fir16_sym_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 1 | 0 | 0 |
| evaluator.evaluate | 8 | 0 | 0 |
| generator.generate | 9 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 7 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 307 | 281 | -8.553 | yes |  |
| 1 | ACCEPT | True | 120 | 292 | 0.183 | yes |  |
| 2 | ACCEPT | True | 85 | 203 | 0.709 | yes |  |
| 3 | ACCEPT | True | 79 | 202 | 1.645 | yes |  |
| 4 | REJECT | True | 178 | 359 | 1.695 |  |  |
| 5 | REJECT | True | 105 | 283 | 1.549 |  |  |
| 6 | ACCEPT | True | 78 | 202 | 1.651 | yes |  |
| 7 | REJECT | True | 78 | 202 | 1.729 |  |  |
| 8 | REJECT | True | 78 | 202 | 1.729 |  |  |

## uart_rx_fifo_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 1 | 0 | 0 |
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 6 | 0 | 0 |
| generator.golden_model | 3 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 70 | 55 | -1.179 | yes |  |
| 1 | ACCEPT | True | 72 | 63 | 0.06 | yes |  |
| 2 | ACCEPT | True | 59 | 63 | 0.042 | yes |  |
| 3 | REJECT | True | 72 | 63 | 0.06 |  |  |
