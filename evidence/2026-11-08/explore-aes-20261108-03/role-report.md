# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| aes128_core_build | module_failed | 5 | 58,802 / 3,527 | — | — | — | golden-model attempts 4 |

## aes128_core_build: module_failed
- error: ValueError: example 0: expected state_out=218805984690271539793496889057209897033, golden model gave 236151275765962226014664816749108529785; example 1: expected state_out=75960790320075369159181001580855561010, golden model gave 229169928561334605677756432564370436314

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| generator.generate | 1 | 0 | 0 |
| generator.golden_model | 4 | 0 | 0 |
