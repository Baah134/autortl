# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| crc16_stream_build | done | 12 | 487,970 / 13,321 | 16 | 16 | ACCEPT 1, REJECT 2 | generator repairs 1, golden-model attempts 1 |
| rr_regfile_build | done | 10 | 381,249 / 11,449 | 42 | 42 | REJECT 2 | golden-model attempts 2 |
| spi_master_build | done | 10 | 450,594 / 11,390 | 28 | 27 | ACCEPT 1, REJECT 2 | — |

## crc16_stream_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.fix | 1 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 16 | 34 | 0.445 | yes |  |
| 1 | REJECT | True | 16 | 34 | 0.445 |  |  |
| 2 | ACCEPT | True | 16 | 18 | 0.445 | yes |  |
| 3 | REJECT | True | 16 | 34 | 0.445 |  |  |

## rr_regfile_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 2 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 2 | 0 | 0 |
| planner.plan | 2 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 42 | 90 | 0.554 | yes |  |
| 1 | REJECT | True | 42 | 93 | 0.569 |  |  |
| 2 | REJECT | True | 50 | 90 | 0.57 |  |  |

## spi_master_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 28 | 37 | 0.331 | yes |  |
| 1 | ACCEPT | True | 27 | 36 | 0.33 | yes |  |
| 2 | REJECT | True | 28 | 35 | 0.343 |  |  |
| 3 | REJECT | True | 27 | 36 | 0.332 |  |  |
