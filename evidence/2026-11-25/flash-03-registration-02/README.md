# flash-03 registration (re-frozen): closed-book single call with Gemini 3.8 Flash-low — November 25, 2026

Supersedes `flash-03-registration-01`, re-frozen the same day before any cell ran: a
probe found the Antigravity CLI updated that evening lingers about 100 s after printing
its result, and the bridge waited for it to exit (`agy_exits_late_after_result`). The
only change is the runtime commit, which now includes the bridge fix; tasks, cells,
model, budgets and analysis are unchanged.

Frozen before any cell ran. It replaces the withdrawn flash-02 plan for a
second model on arm A: flash-01 had web search available through the
Antigravity agent (`docs/DECISIONS.md` 2026-11-21), so it is not a closed-book
single call. This run uses the guarded bridge, which refuses any reply produced
with a tool call. Its numbers are never pooled with `final-02` or `flash-01`.

- **Tasks:** the 40 tasks of `evidence/2026-11-14/final-registration-01`
  (identical list and order to `final-02` and `flash-01`), VerilogEval dataset
  commit c498220d0a52248f8e3fdffe279075215bde2da6.
- **Arm and trials:** `single_call` only, 3 trials, the same budget as
  `final-02` arm A (1 model call). 120 cells, identical to `flash-01`'s cells.
- **Model:** `antigravity.gemini-3.8-flash-low` (Gemini 3.8 Flash, low
  setting), through `scripts/agy_bridge.py` and the Antigravity CLI. The CLI
  reports no model version beyond this name; `observed_model` stays null.
- **Runtime:** `runtime-identity.txt` (commit, tree, runtime SHA-256 =
  sha256 of `autortl-runtime-tree|<tree>`). Cells run from a worktree pinned to
  that commit; the 180 s per-call limit in `llm/routing.yaml` applies.
- **Classification:** a tool-using reply is a failed cell (`MODEL_TOOL_USE`),
  never excluded; quota and timeouts are infrastructure stops, excluded from
  rates and limited to 10% per arm as in `final-02`.
- **Protocol:** `python -m benchmark.campaign --model antigravity.gemini-3.8-flash-low`,
  trial-major, every cell attempted once, never rerun; started only once a
  trivial Flash-low probe through the pinned bridge answers within 30 s (it
  took 105 to 138 s before the bridge fix and 6 s after); grading only after all 120 cells are
  sealed, with the same Icarus grader and report as `final-02`.
- **Comparison:** descriptive, Flash-low arm A against `final-02` arm A (Codex
  default model), paired by task with the task-clustered bootstrap
  (`benchmark/compare.py`). No harness arm is registered here.

`benchmark_registration.json` is the frozen manifest (copied under this name
because the evidence audit treats any `*manifest*` file as an archive manifest).
