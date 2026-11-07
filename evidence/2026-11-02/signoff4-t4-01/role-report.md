# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| crc16_stream_build | done | 12 | 490,058 / 12,755 | 15 | 15 | ACCEPT 2, REJECT 1 | generator repairs 1, golden-model attempts 1 |
| rr_regfile_build | done | 11 | 395,833 / 11,907 | 40 | 40 | REJECT 2 | generator repairs 1, golden-model attempts 2 |
| spi_master_build | done | 10 | 450,847 / 10,354 | 21 | 20 | ACCEPT 2, REJECT 1 | — |

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
| 0 | BASELINE | True | 15 | 34 | 0.432 | yes |  |
| 1 | ACCEPT | True | 15 | 19 | 0.449 | yes |  |
| 2 | REJECT | True | 15 | 34 | 0.432 |  |  |
| 3 | ACCEPT | True | 15 | 18 | 0.318 | yes |  |

## rr_regfile_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 2 | 0 | 0 |
| generator.fix | 1 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 2 | 0 | 0 |
| planner.plan | 2 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 40 | 90 | 0.456 | yes |  |
| 1 | REJECT | True | 46 | 90 | 0.583 |  |  |
| 2 | REJECT | True | 49 | 90 | 0.554 |  |  |

## spi_master_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 21 | 33 | 0.342 | yes |  |
| 1 | ACCEPT | True | 20 | 31 | 0.317 | yes |  |
| 2 | REJECT | True | 20 | 31 | 0.313 |  |  |
| 3 | ACCEPT | True | 20 | 30 | 0.342 | yes |  |
