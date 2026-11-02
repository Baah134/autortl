# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| crc16_stream_build | done | 11 | 438,737 / 14,054 | 16 | 16 | REJECT 3 | golden-model attempts 1 |

## crc16_stream_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 16 | 34 | 0.445 | yes |  |
| 1 | REJECT | True | 16 | 34 | 0.445 |  |  |
| 2 | REJECT | True | 16 | 19 | 0.445 |  |  |
| 3 | REJECT | True | 16 | 34 | 0.445 |  |  |
