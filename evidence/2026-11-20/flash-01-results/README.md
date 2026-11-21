# flash-01 results: Gemini 3.8 Flash, single call — November 20, 2026

Registered before any cell ran (`evidence/2026-11-20/flash-registration-01`).
All 120 cells were attempted once and graded once, after the last was sealed;
nothing was rerun or removed.

## Result

**Gemini 3.8 Flash passes 110 of 120 cells (91.7%; 95% task-clustered
bootstrap CI 83.3% to 98.3%) with one model call per task.** 35 of 40 tasks
pass in all three trials, 2 in none.

This is a single-arm result. The registered comparison with `final-02`
arm A (Codex default model) is paired by task with `benchmark/compare.py`
once `final-02` is graded; it is descriptive, since the runs used different
models and backends and were registered separately.

## Every failing cell

| Task | Trials | What happened |
|---|---|---|
| Prob093_ece241_2014_q3 | 0, 1, 2 | Compiled, 11 mismatches each trial: the same misreading of the specification every time |
| Prob149_ece241_2013_q4 | 0, 1 | No submission: the model call ran past the harness's 180 s per-call timeout (`budget`) |
| Prob149_ece241_2013_q4 | 2 | Compiled, 1,171 mismatches (FSM behaviour wrong) |
| Prob153_gshare | 0, 1 | No submission: per-call timeout (`budget`) |
| Prob137_fsm_serial | 2 | No submission: per-call timeout (`budget`) |
| Prob131_mt2015_q4 | 1 | Compile error |

The five timeouts are counted as failures (intention to treat), as for any
arm. Each ran about 182 s and ended `LLM_BUDGET: model call budget exhausted`: the call hit the harness's per-call timeout (`llm/routing.yaml`
`timeout_s: 180`, the same value `final-02` uses) and the one-call budget allows no retry; the "high" setting of
Flash reasons longer on the FSM and predictor tasks. A longer timeout would be
a different registration.

## Identity

- Model: `antigravity.gemini-3.8-flash-high` via `scripts/agy_bridge.py` and the
  Antigravity CLI; the CLI reports no token usage, so token columns are 0.
- Runtime and registration: `runtime-identity.txt`, `benchmark_registration.json`.
- Grader: Icarus Verilog 12 with the upstream-compatible verdict and a strict
  exit-code check; 0 disagreements.

## Report

### Functional correctness (official testbench, upstream-compatible verdict)

| Arm | Pass | Rate | 95% CI | Always / never pass (tasks) | Missing | Excluded (infrastructure) |
|---|---|---|---|---|---|---|
| A single call | 110/120 | 91.7% | 83.3 to 98.3 | 35 / 2 | 5 | 0 |

### False acceptance (internally accepted, externally failing)

| Arm | Internally accepted | False acceptances | Rate | Cells |
|---|---|---|---|---|
| A single call | 0 | 0 | n/a | none |

Arm A submissions are never internally verified, so it has no accepted set.

### Cost

| Arm | Model calls | Calls per pass | Input tokens | Output tokens | Wall hours |
|---|---|---|---|---|---|
| A single call | 120 | 1.1 | 0 | 0 | 1.3 |

### By category (mean per-task pass rate)

| Category | Tasks | A single call |
|---|---|---|
| combinational_arithmetic | 3 | 100.0% |
| combinational_logic | 21 | 93.7% |
| fsm_control | 6 | 77.8% |
| sequential | 10 | 93.3% |

### Integrity

| Arm | Strict passes | Grader disagreements | Terminations |
|---|---|---|---|
| A single call | 110 | 0 | budget 5, done 115 |

Limits: public tasks do not exclude training contamination; one model and backend; functional correctness only, no area or timing claim; the single-call arm is one backend invocation, not a tools-enabled agent baseline.

## Files

`report.md`/`report.json`, `summary.json` (graded rows), `cells.json` (run
record and verdict per cell), `rtl/` (every sealed design), `campaign.log`,
`runtime-identity.txt`, `benchmark_registration.json`, `archive-manifest.json`.
