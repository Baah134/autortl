# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| axil_regs_build | done | 15 | 671,526 / 19,951 | 95 | 95 | REJECT 3 | golden-model attempts 3 |
| fir16_sym_build | done | 23 | 1,042,998 / 42,656 | 388 | 300 | ACCEPT 4, REJECT 2 | generator repairs 2, golden-model attempts 2 |
| uart_rx_fifo_build | done | 14 | 544,295 / 21,429 | 67 | 58 | ACCEPT 2 | golden-model attempts 3 |

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
| 3 | REJECT | True | 95 | 254 | 5.716 |  |  |

## fir16_sym_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 6 | 0 | 0 |
| generator.fix | 2 | 0 | 0 |
| generator.generate | 7 | 0 | 0 |
| generator.golden_model | 2 | 0 | 0 |
| planner.plan | 6 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 388 | 325 | -11.741 | yes |  |
| 1 | ACCEPT | True | 320 | 372 | 1.386 | yes |  |
| 2 | ACCEPT | True | 305 | 368 | 1.653 | yes |  |
| 3 | ACCEPT | True | 301 | 367 | 1.281 | yes |  |
| 4 | REJECT | True | 304 | 368 | 1.362 |  |  |
| 5 | REJECT | True | 302 | 330 | 1.283 |  |  |
| 6 | ACCEPT | True | 300 | 367 | 1.237 | yes |  |

## uart_rx_fifo_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 2 | 0 | 0 |
| evaluator.evaluate | 2 | 0 | 0 |
| generator.generate | 5 | 0 | 0 |
| generator.golden_model | 3 | 0 | 0 |
| planner.plan | 2 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 67 | 55 | -1.306 | yes |  |
| 1 | ACCEPT | True | 70 | 64 | 0.55 | yes |  |
| 2 | ACCEPT | True | 58 | 63 | 0.042 | yes |  |
