# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| dot4_pipeline_build | done | 9 | 245,718 / 5,168 | 325 | 17 | ACCEPT 1 | golden-model attempts 3 |
| elastic_dot4_build | done | 12 | 510,534 / 13,702 | 328 | 20 | ACCEPT 1, REJECT 2 | golden-model attempts 1 |
| iterative_divider_build | done | 11 | 488,665 / 13,741 | 35 | 31 | ACCEPT 1, REJECT 2 | golden-model attempts 1 |
| signed_fir4_build | done | 11 | 454,108 / 12,618 | 78 | 54 | ACCEPT 2, REJECT 1 | golden-model attempts 1 |
| uart_fifo_build | module_failed | 11 | 202,350 / 17,168 | — | — | — | generator repairs 4, golden-model attempts 2, planner spec attempts 3 |

## dot4_pipeline_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 1 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 3 | 0 | 0 |
| planner.plan | 1 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 325 | 52 | 0.087 | yes |  |
| 1 | ACCEPT | True | 17 | 18 | 0.354 | yes |  |

## elastic_dot4_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 1 | 0 | 0 |
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 328 | 54 | 0.108 | yes |  |
| 1 | ACCEPT | True | 20 | 20 | 0.105 | yes |  |
| 2 | REJECT | True | 20 | 20 | 0.105 |  |  |
| 3 | REJECT | True | 3 | 20 | -0.007 |  |  |

## iterative_divider_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 35 | 57 | 0.315 | yes |  |
| 1 | ACCEPT | True | 31 | 57 | 0.313 | yes |  |
| 2 | REJECT | True | 46 | 50 | 0.313 |  |  |
| 3 | REJECT | True | 33 | 52 | 0.313 |  |  |

## signed_fir4_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 78 | 66 | -0.468 | yes |  |
| 1 | ACCEPT | True | 80 | 67 | 0.183 | yes |  |
| 2 | REJECT | True | 80 | 67 | 0.183 |  |  |
| 3 | ACCEPT | True | 54 | 67 | 0.341 | yes |  |

## uart_fifo_build: module_failed
- error: Testbench failures:
FAIL index=1 signal=tx_ready
FAIL index=1 signal=tx  (x2)

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| generator.fix | 4 | 0 | 0 |
| generator.generate | 2 | 0 | 0 |
| generator.golden_model | 2 | 0 | 0 |
| planner.make_spec | 3 | 0 | 0 |
