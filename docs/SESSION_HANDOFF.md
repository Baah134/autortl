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

**Exact next action:** ROADMAP task B1. When `campaign.log` ends with
`"reason": "all cells attempted"`: `python -m benchmark.report grade`, then
`render`, archive under `evidence/<date>/final-02-results/`, decide the claim
(B2) and put the numbers in the README table (P3). On a stop event, follow
B1's restart notes.

**Done this session**
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
