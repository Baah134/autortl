# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| uart_fifo_build | module_failed | 6 | 103,036 / 9,151 | — | — | — | golden-model attempts 3, planner spec attempts 2 |

## uart_fifo_build: module_failed
- error: ValueError: example 0: expected tx=1, golden model gave 0; example 1: expected tx=1, golden model gave 0

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| generator.generate | 1 | 0 | 0 |
| generator.golden_model | 3 | 0 | 0 |
| planner.make_spec | 2 | 0 | 0 |
