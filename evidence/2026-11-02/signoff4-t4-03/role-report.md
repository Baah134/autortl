# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| crc16_stream_build | done | 12 | 469,534 / 16,686 | 16 | 16 | ACCEPT 1, REJECT 2 | golden-model attempts 2 |
| rr_regfile_build | done | 10 | 381,941 / 11,145 | 42 | 42 | REJECT 2 | golden-model attempts 2 |
| spi_master_build | done | 10 | 451,398 / 10,732 | 19 | 18 | ACCEPT 2, REJECT 1 | — |

## crc16_stream_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 2 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 16 | 34 | 0.445 | yes |  |
| 1 | REJECT | True | 16 | 34 | 0.445 |  |  |
| 2 | ACCEPT | True | 16 | 18 | 0.445 | yes |  |
| 3 | REJECT | True | 19 | 18 | 0.418 |  |  |

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
| 0 | BASELINE | True | 19 | 34 | 0.329 | yes |  |
| 1 | ACCEPT | True | 19 | 32 | 0.343 | yes |  |
| 2 | REJECT | True | 20 | 31 | 0.179 |  |  |
| 3 | ACCEPT | True | 18 | 31 | 0.167 | yes |  |
