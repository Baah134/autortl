# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| aes128_core_build | module_failed | 9 | 106,606 / 8,043 | — | — | — | generator repairs 3, golden-model attempts 4 |

## aes128_core_build: module_failed
- error: Testbench failures:
FAIL index=1 signal=state_out  (x102)

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| generator.fix | 3 | 0 | 0 |
| generator.generate | 2 | 0 | 0 |
| generator.golden_model | 4 | 0 | 0 |
