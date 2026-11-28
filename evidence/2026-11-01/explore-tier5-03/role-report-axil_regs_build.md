# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| axil_regs_build | done | 15 | 665,322 / 20,955 | 95 | 95 | REJECT 3 | golden-model attempts 3 |

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
| 1 | REJECT | True | 136 | 254 | 5.789 |  |  |
| 2 | REJECT | True | 95 | 254 | 5.441 |  |  |
| 3 | REJECT | True | 95 | 254 | 5.716 |  |  |
