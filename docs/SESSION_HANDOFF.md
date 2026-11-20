# AutoRTL current checkpoint

One current section only. History lives in `docs/PROGRESS.md` and Git. The plan
of record is `docs/ROADMAP.md`; the review behind it is
`docs/REVIEW_2026-11-15.md`.

## Current — November 20, 2026: final-02 restarted

Coordinator: Claude. Branch `codex/contract-context`, pushed (`c39826103`).
`main` frozen at `ca61dbc`; no PR yet.

**Running:** `final-02`, the registered comparison (40 tasks x 3 arms x 3
trials = 360 cells, runtime `7731a66d2`). It stalled from November 16 to 20
because the session that launched it ended; it was restarted November 20
08:55 with

    python -m benchmark.campaign --manifest <final-02>/manifest.json --dataset <D> --attempt <final-02> --wait-minutes 20 --max-wait-hours 12

where `<final-02>` is `C:/Users/prince.baah/autortl-private/final-02` and `<D>`
the VerilogEval `dataset_spec-to-rtl` folder (needs `AUTORTL_CODEX_BIN`; ROADMAP
section 3). Progress: `<final-02>/campaign.log`. At restart 66 cells were
sealed; the cell in flight when the session ended (Prob055_conditional full,
trial 0) was sealed `interrupted` and is excluded from rates. The campaign
waits out Codex quota by itself (about 58 cells per usage window); it does
not survive the launching session ending or a reboot. **If
`campaign.log` stops growing and no `waiting_for_model` events appear, run
the same command again.** Expect about 2 to 3 days of awake machine time.

**Do not edit while it runs:** `autortl/`, `llm/`, `data/`, `.claude/skills/`,
`run.py`, `benchmark/pilot.py`, `benchmark/verilogeval.py`. Use a worktree.

**Cleanup branch `c6-dedupe`** (worktree `.claude/worktrees/c6-dedupe`, local
only, 9 commits on `0852295e2`; merge after the campaign because it changes
the runtime): shared synthesis-template blocks (64 scripts byte-identical),
`autortl/fileio.py` helpers for 74 repeated hash/JSON lines, shared tool-path
setup for check scripts, quota-stop label fix, `_finish_optimize` extracted
from `_run_optimize` (491 to 400 lines), ruff lint in CI, pinned requirements
and parallel tests (`-n auto`: 2,345 tests in 4 m 43 s instead of 15 to 22
min). Both suites green on the branch.

**Exact next action:** ROADMAP task B1. When `campaign.log` ends with
`"reason": "all cells attempted"`, run `python -m benchmark.finish` (full
command in B1): it grades, reports, applies the claim rule registered
November 20 (`docs/DECISIONS.md`, `benchmark/claim.py`), archives to
`evidence/<date>/final-02-results/`, writes the README, seals, audits and
prints the README row (P3). Then follow `docs/RELEASE.md`. On a stop event,
follow B1's restart notes.

**Done this session**
- Decision rule registered before grading (123 of 360 cells sealed, none
  graded); `benchmark/claim.py`, `benchmark/finish.py` with tests;
  release checklist, PR and release-note drafts in `docs/RELEASE.md`.
- `final-01` aborted after 5 cells on `empty_netlist_unplaceable`; fixed with
  tests and live checks; a synthesis sweep of all 40 final references passes
  39/40 (the exception is a reference with latches). Evidence
  `evidence/2026-11-15/empty-netlist-01`.
- Full suites green after the fix and cleanup: 2,330 harness, 323 tooling.
- Review (`docs/REVIEW_2026-11-15.md`), roadmap, `benchmark/campaign.py`,
  `benchmark/report.py`, `scripts/lease_keeper.py`.
- Repository cleanup: one `AGENTS.md`; slim `CLAUDE.md`, `GEMINI.md`,
  `START_HERE.md`; README 149 lines with `docs/RESULTS.md` and
  `docs/USAGE.md`; superseded docs in `docs/archive/`.

**Open:** owner decisions (PR and merge to `main`, B3 task source, pinned
model, board authorisation); research risk
`planner_spec_error_shared_by_oracle_and_rtl` (ROADMAP V1); Codex's parked
November 13 candidate-export stage in
`C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work/nov13-candidate-bundle-stage`.

**Environment:** ROADMAP section 3. Keep the machine awake; renew the lease
with `python scripts/lease_keeper.py --token-file <private file>`.
