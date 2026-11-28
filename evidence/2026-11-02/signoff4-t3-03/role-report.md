# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| dot4_pipeline_build | done | 9 | 246,526 / 4,509 | 325 | 17 | ACCEPT 1 | golden-model attempts 3 |
| elastic_dot4_build | done | 11 | 469,271 / 10,464 | 328 | 20 | ACCEPT 1, REJECT 2 | golden-model attempts 1 |
| iterative_divider_build | done | 11 | 498,002 / 11,665 | 68 | 26 | ACCEPT 3 | golden-model attempts 1 |
| signed_fir4_build | done | 12 | 498,210 / 15,087 | 78 | 71 | ACCEPT 2, REJECT 1 | golden-model attempts 1 |
| uart_fifo_build | module_failed | 7 | 128,618 / 12,824 | — | — | — | generator repairs 3, golden-model attempts 1, planner spec attempts 2 |

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
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 328 | 54 | 0.108 | yes |  |
| 1 | ACCEPT | True | 20 | 20 | 0.105 | yes |  |
| 2 | REJECT | True | 20 | 20 | 0.105 |  |  |
| 3 | REJECT | True | 20 | 20 | 0.105 |  |  |

## iterative_divider_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 68 | 81 | 0.302 | yes |  |
| 1 | ACCEPT | True | 67 | 74 | 0.313 | yes |  |
| 2 | ACCEPT | True | 30 | 45 | 0.175 | yes |  |
| 3 | ACCEPT | True | 26 | 38 | 0.231 | yes |  |

## signed_fir4_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| doctor.surgery | 1 | 0 | 0 |
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 78 | 66 | -0.316 | yes |  |
| 1 | ACCEPT | True | 80 | 67 | 0.301 | yes |  |
| 2 | ACCEPT | True | 71 | 67 | 0.31 | yes |  |
| 3 | REJECT | True | 69 | 66 | -0.22 |  |  |

## uart_fifo_build: module_failed
- error: Testbench failures:
FAIL index=1 signal=data_out  (x65)
FAIL index=1 signal=valid_out  (x7)
FAIL index=67 signal=in_ready

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| generator.fix | 3 | 0 | 0 |
| generator.generate | 1 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.make_spec | 2 | 0 | 0 |
