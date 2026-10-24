# Previous-proposal context: exploratory paired study

Exploratory context-only feedback ablation; n=3pairs, actual CLI model identity unknown. Not a controlled model-strength or product comparison.

| Pair | Context | Status | Winner LUT / FF | Calls | Repeat proposals | Tool seconds | Wall seconds | Independent |
|---|---|---|---|---|---|---|---|---|
| 1 | off | done | 33 / 46 | 9 | 1 | 308.799 | 453.781 | True |
| 1 | on | done | 32 / 50 | 8 | 1 | 284.719 | 417.578 | True |
| 2 | off | model_blocked | unknown / unknown | 6 | 1 | 192.985 | 274.922 | False |
| 2 | on | done | 33 / 46 | 8 | 1 | 377.472 | 510.891 | True |
| 3 | off | done | 33 / 46 | 8 | 1 | 812.937 | 938.078 | True |
| 3 | on | done | 33 / 46 | 8 | 1 | 735.093 | 843.984 | True |

No established repetition benefit; disable default advisory context and retain opt-in experiment/audit records. Interrupted trials and unknown usage prevent a complete efficacy comparison. Investigate stale plan/source binding separately.

## Predeclared criteria

- all_six_trials_retained: True
- uninterrupted_comparison_available: False
- repetition_decreased: False
- completion_not_lower: True
- no_unscored_generated_outcomes: True
- cost_known_and_within_predeclared_25pct: False

## Limits

- Unknown underlying model identity
- Three pairs and one curated design
- All supplied independent checks retained; selected widths are not formal all-domain proof
- Reported tokens are counts, not monetary costs; cached tokens are a subset of input counts
- Baseline WIDTH1 source warning may remain despite actual Vivado PASS; no cross-tool portability claim
- Invalid study01 setup retained separately with lower-bound budget, excluded from paired efficacy counts
- Original pair2 baseline quota interruption is retained; supplemental same-runtime recovery is not substituted into the paired rows
- Host load and power state were uncontrolled; isolated synthetic staging tests overlapped part of pair3 baseline. Wall/tool costs are descriptive, not causal efficiency estimates
