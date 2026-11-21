# flash-02 registration: harness arms with Gemini 3.8 Flash — November 20, 2026

Frozen before any cell ran. The second half of the Flash comparison: the
same harness arms as `final-02`, driven by Gemini 3.8 Flash instead of the
Codex default model. Together with `flash-01` (Flash, single call) it asks
whether the harness changes a different model's pass rate the way it changes
Codex's. Separate attempt; never pooled with `final-02` or `flash-01`.

- **Tasks:** the 40 registered final tasks, same list and order as `final-02`.
- **Arms:** `ablation` (B) and `full` (C), 3 trials each, 240 cells; the same
  budgets (16 model calls, 1,500 tool seconds, 2,100 wall seconds per cell)
  and arm C settings (one candidate, one iteration, out of context) as `final-02`.
- **Model:** `antigravity.gemini-3.8-flash-high` via `scripts/agy_bridge.py`.
- **Runtime:** `runtime-identity.txt`. It launches only after `final-02`
  finishes (so the two never compete for Vivado time) and before the
  `c6-dedupe` cleanup merges, so the harness code matches `final-02`'s.
- **Protocol:** `python -m benchmark.campaign --model antigravity.gemini-3.8-flash-high --wait-minutes 20`,
  trial-major, every cell attempted once, never rerun; graded only after all
  240 are sealed.
- **Analysis (descriptive):** Flash C minus Flash A (`flash-01`) paired by
  task, beside Codex C minus Codex A (`final-02`); with `benchmark.report`
  for the within-model arms and `benchmark/compare.py` across runs. The
  `final-02` decision rule (`docs/DECISIONS.md`) governs only `final-02`.
