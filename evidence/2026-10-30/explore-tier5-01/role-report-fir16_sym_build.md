# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| fir16_sym_build | done | 15 | 657,904 / 32,676 | 394 | 165 | ACCEPT 2, REJECT 1 | generator repairs 1, golden-model attempts 1 |

## fir16_sym_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 3 | 0 | 0 |
| evaluator.evaluate | 3 | 0 | 0 |
| generator.fix | 1 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 394 | 325 | -10.77 | yes |  |
| 1 | ACCEPT | True | 160 | 261 | -3.7 | yes |  |
| 2 | ACCEPT | True | 165 | 262 | -3.024 | yes |  |
| 3 | REJECT | True | 394 | 325 | -10.77 |  |  |
