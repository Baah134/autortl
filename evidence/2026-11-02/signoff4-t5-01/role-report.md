# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| axil_regs_build | done | 17 | 739,397 / 24,751 | 95 | 95 | REJECT 3 | generator repairs 1, golden-model attempts 4 |
| fir16_sym_build | done | 24 | 1,136,524 / 40,445 | 166 | 159 | ACCEPT 2, REJECT 5 | generator repairs 1, golden-model attempts 1 |
| uart_rx_fifo_build | done | 18 | 707,328 / 28,264 | 63 | 58 | ACCEPT 2, REJECT 1 | generator repairs 2, golden-model attempts 3 |

## axil_regs_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.fix | 1 | 0 | 0 |
| generator.generate | 6 | 0 | 0 |
| generator.golden_model | 4 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 95 | 254 | 5.441 | yes |  |
| 1 | REJECT | True | 95 | 254 | 5.716 |  |  |
| 2 | REJECT | True | 95 | 254 | 5.441 |  |  |
| 3 | REJECT | True | 136 | 254 | 5.789 |  |  |

## fir16_sym_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 1 | 0 | 0 |
| evaluator.evaluate | 7 | 0 | 0 |
| generator.fix | 1 | 0 | 0 |
| generator.generate | 8 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 6 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 166 | 325 | -17.628 | yes |  |
| 1 | ACCEPT | True | 161 | 317 | 0.197 | yes |  |
| 2 | REJECT | True | 154 | 261 | -0.038 |  |  |
| 3 | REJECT | True | 166 | 289 | 0.002 |  |  |
| 4 | REJECT | True | 388 | 522 | 0.877 |  |  |
| 5 | REJECT | True | 161 | 317 | 0.197 |  |  |
| 6 | REJECT | True | 161 | 317 | 0.197 |  |  |
| 7 | ACCEPT | True | 159 | 317 | 0.214 | yes |  |

## uart_rx_fifo_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 1 | 0 | 0 |
| evaluator.evaluate | 3 | 0 | 0 |
| generator.fix | 2 | 0 | 0 |
| generator.generate | 6 | 0 | 0 |
| generator.golden_model | 3 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 63 | 55 | -1.2 | yes |  |
| 1 | ACCEPT | True | 65 | 64 | 0.459 | yes |  |
| 2 | REJECT | True | 69 | 59 | 0.551 |  |  |
| 3 | ACCEPT | True | 58 | 64 | 0.544 | yes |  |
