# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| aes128_core_build | module_failed | 5 | 87,031 / 6,574 | — | — | — | golden-model attempts 4 |
| cordic_build | done | 20 | 809,387 / 25,077 | 155 | 194 | ACCEPT 2, REJECT 2 | golden-model attempts 4 |
| rv32i_core_build | done | 24 | 1,100,337 / 37,861 | 2139 | 1992 | ACCEPT 3, REJECT 1 | golden-model attempts 6 |

## aes128_core_build: module_failed
- error: ValueError: IndexError: list index out of range

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| generator.generate | 1 | 0 | 0 |
| generator.golden_model | 4 | 0 | 0 |

## cordic_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 1 | 0 | 0 |
| evaluator.evaluate | 4 | 0 | 0 |
| generator.generate | 8 | 0 | 0 |
| generator.golden_model | 4 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 155 | 62 | -1.759 | yes |  |
| 1 | ACCEPT | True | 195 | 94 | -0.279 | yes |  |
| 2 | ACCEPT | True | 194 | 95 | 0.076 | yes |  |
| 3 | REJECT | True | 195 | 95 | 0.153 |  |  |
| 4 | REJECT | True | 195 | 95 | 0.153 |  |  |

## rv32i_core_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 4 | 0 | 0 |
| generator.generate | 10 | 0 | 0 |
| generator.golden_model | 6 | 0 | 0 |
| planner.plan | 4 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 2139 | 4357 | 0.694 | yes |  |
| 1 | ACCEPT | True | 2137 | 4357 | 0.449 | yes |  |
| 2 | ACCEPT | True | 2030 | 4357 | 0.41 | yes |  |
| 3 | ACCEPT | True | 1992 | 4357 | 0.526 | yes |  |
| 4 | REJECT | True | 1993 | 4357 | 0.597 |  |  |
