# VerilogEval spec-to-RTL: single call vs AutoRTL (40 tasks x 3 trials)

Archived by `python -m benchmark.finish`. Numbers, claim and tables below are generated from the sealed cells; nothing was rerun or removed.

## Claim (pre-registered rule, docs/DECISIONS.md 2026-11-20)

**Verdict: `single_call_better`.** A single model call passes more tasks than the full harness: C 86.1% vs A 94.1%, difference -9.2 pp (95% CI -19.2 to -0.8 pp, 40 tasks); the harness used 7.4x the model calls per pass.

Disclosures required by the rule:

- 2 cell(s) of single_call were stopped by infrastructure and are excluded from rates.
- 2 cell(s) of ablation were stopped by infrastructure and are excluded from rates.
- 5 cell(s) of full were stopped by infrastructure and are excluded from rates.
- ablation: 10 of 110 internally accepted designs fail the official testbench (Prob066_edgecapture#1, Prob070_ece241_2013_q2#1, Prob093_ece241_2014_q3#0, Prob093_ece241_2014_q3#1, Prob093_ece241_2014_q3#2, Prob139_2013_q2bfsm#0, Prob139_2013_q2bfsm#1, Prob149_ece241_2013_q4#0, Prob149_ece241_2013_q4#1, Prob149_ece241_2013_q4#2).
- ablation: false acceptance above 5%, so internal acceptance is not a reliable correctness signal on these tasks.
- full: 11 of 110 internally accepted designs fail the official testbench (Prob027_fadd#2, Prob066_edgecapture#0, Prob066_edgecapture#1, Prob066_edgecapture#2, Prob093_ece241_2014_q3#0, Prob093_ece241_2014_q3#1, Prob093_ece241_2014_q3#2, Prob139_2013_q2bfsm#0, Prob139_2013_q2bfsm#1, Prob149_ece241_2013_q4#0, Prob149_ece241_2013_q4#2).
- full: false acceptance above 5%, so internal acceptance is not a reliable correctness signal on these tasks.

Secondary comparisons (descriptive):

- full minus ablation: +0.4 pp (95% CI -5.0 to +5.8), reading `no_material_difference`
- ablation minus single_call: -9.6 pp (95% CI -18.3 to -2.5), reading `single_call_better`

## Identity

- Dataset: VerilogEval spec-to-RTL, commit `c498220d0a52248f8e3fdffe279075215bde2da6`
- Runtime: commit `7731a66d273b2d29fc78a27e435fd181e3c69b70`, sha256 `86eb1dba3c2b2f50a14f080b845b4540ee528c872b73c32d333a7e036e860b95`
- Requested model: `unobserved-cli-default`; observed: `None`
- Tasks 40, graded cells 360; registration copied as `benchmark_registration.json`

## Protocol

Arms A (single call), B (harness without generated-testbench mutation qualification) and C (full harness), three trials per task, run trial-major by `benchmark.campaign`; a cell is attempted once and never rerun. Grading with the official testbench (Icarus Verilog 12, upstream-compatible verdict) started only after every cell was sealed. Intervals are task-clustered bootstrap.

## Non-`done` terminations

- `Prob019_m2014_q4f-single_call-2`: termination `model_blocked`, grade `missing`
- `Prob042_vector4-full-1`: termination `interrupted`, grade `missing`
- `Prob055_conditional-full-0`: termination `interrupted`, grade `missing`
- `Prob065_7420-ablation-1`: termination `interrupted`, grade `missing`
- `Prob065_7420-single_call-0`: termination `model_blocked`, grade `missing`
- `Prob070_ece241_2013_q2-ablation-0`: termination `interrupted`, grade `missing`
- `Prob070_ece241_2013_q2-full-0`: termination `interrupted`, grade `missing`
- `Prob078_dualedge-ablation-1`: termination `failed`, grade `missing`
- `Prob115_shift18-ablation-1`: termination `failed`, grade `missing`
- `Prob131_mt2015_q4-ablation-0`: termination `failed`, grade `missing`
- `Prob131_mt2015_q4-ablation-1`: termination `failed`, grade `missing`
- `Prob131_mt2015_q4-ablation-2`: termination `failed`, grade `missing`
- `Prob131_mt2015_q4-full-0`: termination `failed`, grade `missing`
- `Prob131_mt2015_q4-full-1`: termination `failed`, grade `missing`
- `Prob131_mt2015_q4-full-2`: termination `failed`, grade `missing`
- `Prob139_2013_q2bfsm-full-2`: termination `interrupted`, grade `missing`
- `Prob149_ece241_2013_q4-full-1`: termination `interrupted`, grade `missing`
- `Prob153_gshare-ablation-0`: termination `failed`, grade `missing`
- `Prob153_gshare-ablation-1`: termination `failed`, grade `missing`
- `Prob153_gshare-ablation-2`: termination `failed`, grade `missing`
- `Prob153_gshare-full-0`: termination `failed`, grade `missing`
- `Prob153_gshare-full-1`: termination `failed`, grade `missing`

## Report

40 tasks, 360 graded cells. Intervals are 95% task-clustered bootstrap (10000 resamples, seed 20261115); trials of one task are not independent. Missing submissions count as failures; cells stopped by infrastructure (model quota, interruption) are not verdicts and are excluded from rates.

### Functional correctness (official testbench, upstream-compatible verdict)

| Arm | Pass | Rate | 95% CI | Always / never pass (tasks) | Missing | Excluded (infrastructure) |
|---|---|---|---|---|---|---|
| A single call | 111/118 | 94.1% | 86.7 to 100.0 | 37 / 2 | 0 | 2 |
| B ablation | 100/118 | 84.7% | 74.2 to 93.3 | 31 / 4 | 8 | 2 |
| C full harness | 99/115 | 86.1% | 73.3 to 94.2 | 33 / 5 | 5 | 5 |

### Paired differences (same tasks; percentage points)

| Comparison | Mean difference | 95% CI | Tasks better / equal / worse |
|---|---|---|---|
| C full harness minus A single call | -9.2 | -19.2 to -0.8 | 1 / 34 / 5 |
| C full harness minus B ablation | +0.4 | -5.0 to +5.8 | 4 / 33 / 3 |
| B ablation minus A single call | -9.6 | -18.3 to -2.5 | 0 / 34 / 6 |

An interval that includes 0 does not show a difference.

### False acceptance (internally accepted, externally failing)

| Arm | Internally accepted | False acceptances | Rate | Cells |
|---|---|---|---|---|
| A single call | 0 | 0 | n/a | none |
| B ablation | 110 | 10 | 9.1% | Prob066_edgecapture#1, Prob070_ece241_2013_q2#1, Prob093_ece241_2014_q3#0, Prob093_ece241_2014_q3#1, Prob093_ece241_2014_q3#2, Prob139_2013_q2bfsm#0, Prob139_2013_q2bfsm#1, Prob149_ece241_2013_q4#0, Prob149_ece241_2013_q4#1, Prob149_ece241_2013_q4#2 |
| C full harness | 110 | 11 | 10.0% | Prob027_fadd#2, Prob066_edgecapture#0, Prob066_edgecapture#1, Prob066_edgecapture#2, Prob093_ece241_2014_q3#0, Prob093_ece241_2014_q3#1, Prob093_ece241_2014_q3#2, Prob139_2013_q2bfsm#0, Prob139_2013_q2bfsm#1, Prob149_ece241_2013_q4#0, Prob149_ece241_2013_q4#2 |

Arm A submissions are never internally verified, so it has no accepted set.

### Cost

| Arm | Model calls | Calls per pass | Input tokens | Output tokens | Wall hours |
|---|---|---|---|---|---|
| A single call | 120 | 1.1 | 1,340,327 | 17,674 | 0.2 |
| B ablation | 812 | 8.1 | 19,881,590 | 368,453 | 10.6 |
| C full harness | 792 | 8.0 | 19,516,749 | 354,596 | 10.7 |

### By category (mean per-task pass rate)

| Category | Tasks | A single call | B ablation | C full harness |
|---|---|---|---|---|
| combinational_arithmetic | 3 | 100.0% | 100.0% | 88.9% |
| combinational_logic | 21 | 95.2% | 88.1% | 90.5% |
| fsm_control | 6 | 83.3% | 72.2% | 66.7% |
| sequential | 10 | 96.7% | 80.0% | 83.3% |

### Integrity

| Arm | Strict passes | Grader disagreements | Terminations |
|---|---|---|---|
| A single call | 111 | 0 | done 118, model_blocked 2 |
| B ablation | 100 | 0 | done 110, failed 8, interrupted 2 |
| C full harness | 99 | 0 | done 110, failed 5, interrupted 5 |

Limits: public tasks do not exclude training contamination; one model and backend; functional correctness only, no area or timing claim; the single-call arm is one backend invocation, not a tools-enabled agent baseline.

## Files

`report.md`/`report.json` (statistics), `claim.json` (rule output), `summary.json` (graded rows), `cells.json` (run record, verdict and run summary per cell), `rtl/` (every sealed design), `campaign.log`, `runtime-identity.txt`, `benchmark_registration.json`, `archive-manifest.json` (SHA-256 of every file).
