# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| dot4_pipeline_build | done | 9 | 245,518 / 4,821 | 325 | 17 | ACCEPT 1 | golden-model attempts 3 |
| elastic_dot4_build | done | 11 | 469,132 / 9,985 | 328 | 3 | ACCEPT 2, REJECT 1 | golden-model attempts 1 |
| iterative_divider_build | done | 11 | 490,551 / 11,690 | 38 | 26 | ACCEPT 2, REJECT 1 | golden-model attempts 1 |
| signed_fir4_build | done | 11 | 457,698 / 12,386 | 79 | 81 | ACCEPT 1, REJECT 2 | golden-model attempts 1 |
| uart_fifo_build | module_failed | 7 | 128,730 / 13,935 | — | — | — | generator repairs 3, golden-model attempts 1, planner spec attempts 2 |

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
| 3 | ACCEPT | True | 3 | 20 | 0.134 | yes |  |

## iterative_divider_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 38 | 47 | 0.313 | yes |  |
| 1 | ACCEPT | True | 30 | 40 | 0.315 | yes |  |
| 2 | REJECT | True | 38 | 45 | 0.313 |  |  |
| 3 | ACCEPT | True | 26 | 39 | 0.277 | yes |  |

## signed_fir4_build: done

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| evaluator.evaluate | 3 | 0 | 0 |
| generator.generate | 4 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.plan | 3 | 0 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 79 | 66 | -0.432 | yes |  |
| 1 | ACCEPT | True | 81 | 67 | 0.333 | yes |  |
| 2 | REJECT | True | 82 | 67 | 0.337 |  |  |
| 3 | REJECT | True | 83 | 67 | 0.337 |  |  |

## uart_fifo_build: module_failed
- error: Testbench failures:
FAIL index=3 signal=out_data  (x59)
FAIL index=3 signal=out_valid  (x3)
FAIL index=67 signal=in_ready  (x3)

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| generator.fix | 3 | 0 | 0 |
| generator.generate | 1 | 0 | 0 |
| generator.golden_model | 1 | 0 | 0 |
| planner.make_spec | 2 | 0 | 0 |
