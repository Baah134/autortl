# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| counter | model_blocked | 1 | 0 / 0 | — | — | — | — |
| mux4 | model_blocked | 1 | 0 / 0 | — | — | — | — |

## counter: model_blocked
- error: CODEX_UNAVAILABLE: role 'planner': CODEX_UNAVAILABLE: worker could not launch

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| planner.plan | 0 | 1 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 55 | 37 | 0.494 | yes |  |

## mux4: model_blocked
- error: CODEX_UNAVAILABLE: role 'planner': CODEX_UNAVAILABLE: worker could not launch

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| planner.plan | 0 | 1 | 0 |

| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |
|---:|---|---|---:|---:|---:|---|---|
| 0 | BASELINE | True | 8 | 8 | 0.579 | yes |  |
