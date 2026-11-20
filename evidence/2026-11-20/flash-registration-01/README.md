# flash-01 registration: single-call arm with Gemini 3.8 Flash — November 20, 2026

Frozen before any cell ran. A second model on the registered final task set,
to compare models on arm A (one model call, no harness). It is a separate
attempt: its numbers are never pooled with `final-02`.

- **Tasks:** the 40 tasks of `evidence/2026-11-14/final-registration-01`
  (identical list and order to `final-02`), VerilogEval dataset commit
  c498220d0a52248f8e3fdffe279075215bde2da6.
- **Arm and trials:** `single_call` only, 3 trials, the same budget as
  `final-02` arm A (1 model call). 120 cells.
- **Model:** `antigravity.gemini-3.8-flash-high` (Gemini 3.8 Flash, high
  setting), through `scripts/agy_bridge.py` and the Antigravity CLI. The CLI
  reports no model version beyond this name; `observed_model` stays null.
- **Runtime:** `runtime-identity.txt` (commit, tree, runtime SHA-256 =
  sha256 of `autortl-runtime-tree|<tree>`).
- **Protocol:** `python -m benchmark.campaign --model antigravity.gemini-3.8-flash-high`,
  trial-major, every cell attempted once, never rerun; grading only after all
  120 cells are sealed, with the same Icarus grader and report as `final-02`.
- **Comparison:** descriptive, Flash arm A against `final-02` arm A (Codex
  default model), paired by task with the task-clustered bootstrap. The
  harness arms for Flash are a later, separately registered attempt, run
  after `final-02` so the two do not compete for Vivado time.

`benchmark_registration.json` is the frozen manifest (copied under this name
because the evidence audit treats any `*manifest*` file as an archive manifest).
