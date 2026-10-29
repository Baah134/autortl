# 24-hour plan (from October 29, 2026)

Owner: Claude Code as supervisor. The harness's roles do all design work;
the supervisor runs the harness, reads the roles' logs, and turns every
observed failure into a taxonomy entry and then a harness or role fix.
Status is tracked at the end of this file.

## Ground rules

- **One bench at a time.** Vivado runs are sequential, and so are benches:
  `curriculum.runner.run_tier` reads the history at the start and rewrites
  it at the end, so two concurrent benches would drop a record (fixed in
  phase 3).
- **Taxonomy first.** Every new failure mode is recorded in
  `data/taxonomy.yaml` in its own commit before the fix.
- **Batch harness changes.** Any frozen-source change starts a new cohort for
  every tier, so fixes are batched between gate series, never in the middle
  of one.
- **Pinned model.** From the merge of `claude/model-portability` on, every
  gate pins its model (`--model`), so the model is part of the cohort.
  The main series uses `gpt-6-luna`, the Codex default today.
- **Before every push:** the full suite, `tools/evidence_audit.py --rev HEAD`,
  and, for a harness change, a tier0 gate on the new identity.
- **Evidence.** Every run is archived under `evidence/<date>/<name>/` with a
  README and a hash manifest, failures included.

## Phase 1 (hours 0-2): land model portability, re-hold tier0

1. Finish and archive `tier1-campaign-01` (old identity): counter8 PASS,
   debouncer FAIL at spec lint, encoder8 PASS (6 → 5 LUTs), pwm pending.
2. Fast-forward `claude/model-portability` (5 taxonomy entries, 5 fixes,
   gate `--model`, README rework). Full suite (1,511), audit, push.
3. Three tier0 gates on the new identity with `--model gpt-6-luna`
   (about 13 minutes each). Goal: tier0 held again, now with a known model.
4. Fast-forward `main`.

## Phase 2 (hours 2-6): tier1 held

5. Tier1 gate on the new identity. Read every role's journal: planner
   specs, golden attempts, generator repairs, evaluator verdicts.
6. Triage each failure: taxonomy entry, fix, tests. Batch them.
7. Re-gate tier0 once after the batch, then run tier1 until three
   consecutive qualifying runs. Goal: tier1 held.

## Phase 3 (in parallel with Vivado runs): supervisor tooling

8. `tools/role_report.py`: per-role calls, failures, repair counts,
   rejected-candidate reasons and verdicts, from any run or campaign
   folder. This is how role quality is measured from now on.
9. Make the curriculum history append-safe under concurrent benches
   (taxonomy entry first), with a test that runs two benches at once.

## Phase 4 (hours 6-9): model matrix

10. Tier0, then tier1, with `gpt-5.6-luna` (the oldest, smallest listed
    model), `gpt-6.1-sol` and `gpt-6-astra`. Same budgets.
11. `docs/MODEL_MATRIX.md`: pass rate, model calls, LUT results and the
    role failures each model hits. Fix the role failures the weaker models
    expose, in one batch.

## Phase 5 (hours 9-16): tier2

12. Tier2 gate (fir8 optimize; packet FIFO, skid buffer and sync FIFO
    builds), triage, fixes, and runs toward three consecutive. Goal:
    tier2 held, or a documented blocker per entry.

## Phase 6 (hours 16-22): tier3 and the timing objective

13. One full tier3 run (dot4 pipeline, elastic dot4, divider, signed FIR,
    UART FIFO), triaged like the rest.
14. Decide `io_dominated_timing_metric`: report out-of-context
    register-to-register slack beside the I/O-limited harness slack, as an
    advisory metric, without changing acceptance.

## Phase 7 (hours 22-24): publish

15. Update the README results, PROGRESS, SESSION_HANDOFF and TASKS. Audit,
    push, fast-forward `main`, hand the lease off with a mailbox note.

## Status

| Step | State | Evidence |
|---|---|---|
| 1 | running | logs/tier1-campaign-01 |
