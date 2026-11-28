# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| axil_regs_build | baseline_failed | 10 | 183,538 / 12,721 | — | — | — | generator repairs 4, golden-model attempts 3 |

## axil_regs_build: baseline_failed
- error: Testbench failures:
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=5
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=5
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=6
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=6
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=7
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=7
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=8
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=8
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=9
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=9
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=10
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=10
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=11
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=11
FAIL BEHAVIOR rule=rdata_register_value_or_stall_hold cycle=14

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| generator.fix | 4 | 0 | 0 |
| generator.generate | 3 | 0 | 0 |
| generator.golden_model | 3 | 0 | 0 |
