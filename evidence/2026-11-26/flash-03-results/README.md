# flash-03 results: Gemini 3.8 Flash-low, closed-book single call — November 26, 2026

Registered before any cell ran (`evidence/2026-11-25/flash-03-registration-02`,
runtime `202a6daa6`). All 120 cells were attempted once, from a worktree pinned
to that runtime, and graded once after the last was sealed; nothing was rerun
or removed. The guarded bridge refuses tool-using replies; none occurred.

## Result

**Gemini 3.8 Flash-low passes 103 of 120 cells (85.8%; 95% task-clustered
bootstrap CI 75.8% to 94.2%) with one model call per task.** 32 of 40 tasks
pass in all three trials, 1 in none. Every cell ended `done`: no timeouts, no
quota stops, no compile errors; all 17 failures are wrong behaviour.

Paired with `final-02` arm A (Codex default model, 94.1%), Flash-low is
8.3 points lower (95% CI -15.8 to -1.7; 1 task better, 33 equal, 6 worse;
`comparison-with-final-02.md`). The comparison is descriptive: different
model, backend and week, registered separately (`docs/DECISIONS.md`
2026-11-25). It says nothing about the harness, which was not run here.

## Every failing cell

| Task | Trials | Mismatches |
|---|---|---|
| Prob093_ece241_2014_q3 | 0, 1, 2 | 11 each (official reference contradicts its own Karnaugh map; every final-02 arm fails it too) |
| Prob149_ece241_2013_q4 | 0, 1 | 1,171 and 873 (reference contradicts its prose; trial 2 passed) |
| Prob066_edgecapture | 0, 2 | 91 each |
| Prob139_2013_q2bfsm | 0, 1 | 198 each |
| Prob070_ece241_2013_q2 | 1, 2 | 17 and 3 (don't-care cover) |
| Prob057_kmap2 | 1, 2 | 14 and 47 |
| Prob078_dualedge | 0, 2 | 223 each |
| Prob137_fsm_serial | 0, 2 | 72 each |

On Prob066 and Prob139 Flash-low fails with exactly the mismatch counts of the
final-02 harness cells (91/266 and 198/1002), which the failure review traced
to the planner clearing a history register on reset and sampling an input one
cycle early. A model reading the prose directly makes the same readings, so
these are ambiguities of the task text that Codex's single call happened to
resolve the reference's way, not errors only the harness pipeline makes.

## Files

`report.md` (rates, cost, categories, integrity), `cells.json` (every cell's
receipt and verdict), `rtl/` (every submission), `campaign.log`,
`benchmark_registration.json`, `runtime-identity.txt`,
`comparison-with-final-02.md`; `archive-manifest.json` hashes them all.
`benchmark.finish` graded, reported and archived the run, then stopped at the
claim step, which needs a harness arm that this registration does not have.
