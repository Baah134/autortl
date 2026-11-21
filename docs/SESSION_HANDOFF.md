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

where `<final-02>` is `C:/Users/<user>/autortl-private/final-02` and `<D>`
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
only; brought up to date with this branch November 20 (merge `ce4fc4c93`, suites green: 2,369 harness, 323 tooling, lint clean); merge after the campaign because it changes
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
**`flash-02` is withdrawn (0 cells run) and its watcher was stopped on
November 21. Do not start it.** `agy` gives Gemini web search and shell tools,
and Flash-high's planner calls exceed the 180 s limit (`docs/DECISIONS.md`
2026-11-21). The bridge now refuses tool-using replies. A new Flash run needs
a new registration with Flash-low or medium. Merge `c6-dedupe` and then
`bench-fixes` once final-02 is graded; the release (P2/P5) does not wait for
any Flash run.

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

**Failure review so far (internal logs only, no official verdicts; file the
taxonomy entries after the campaign, `data/` is frozen):** of 169 sealed
final-02 cells, 6 harness cells ended `failed`, from two causes, each the same
in arms B and C, so the comparison is unaffected between them:
- `Prob131_mt2015_q4` (4 cells): the planner splits the request into
  submodules and `fsm.py` stops with "Multi-module build requires trusted
  integration testbench" (`build_blocked`); VerilogEval supplies no trusted
  testbench to the harness. A harness limit, already disclosed; recurs every
  trial. Candidate fix after release: force a single-module plan when the
  request names one top and no submodules.
- `Prob153_gshare` (2 cells): the generated golden model computes
  `predict_taken`/`predict_history` from the state after the clock edge,
  while the testbench (fixed_latency 0) samples before it; outputs are Mealy
  (current `predict_pc` with pre-edge history). Every RTL fix then fails the
  oracle from sample 1 (identical 17 + 89 mismatches in both arms).
  Recurrence of `fixed_latency_observation_ambiguous`; the repair must reach
  the golden-model prompt (latency 0 means outputs from the pre-edge state and
  current inputs), not only the planner.

**Both causes fixed on local branch `bench-fixes`** (worktree
`.claude/worktrees/bench-fixes`, `2b5caf87a`, built on `c6-dedupe`; suites
green, 2,371 harness and 323 tooling, lint clean). It includes the taxonomy
entries and `docs/DECISIONS.md` 2026-11-21: final-02 is reported as run, and
later numbers on its tasks are labelled tuned. A live check with Flash-high
(`autortl-private/fixcheck-01`) never reached either fix because both planner
calls timed out, so the fixes are not yet checked live. Merge it after `c6-dedupe`,
once flash-02 ends. On November 21, 19 stale agent worktrees (already merged,
nothing uncommitted) were removed and their branches kept;
`agent-a68f849245229e7f6` has uncommitted changes and was left in place.

**flash-01 done, but not closed-book:** Gemini 3.8 Flash through the
Antigravity agent, 110/120 (91.7%, CI 83.3 to 98.3); 5 cells hit the 180 s
call timeout. Web search was available to the model, so it is not compared
with Codex arm A (`docs/DECISIONS.md` 2026-11-21). Evidence
`evidence/2026-11-20/flash-01-results`. `benchmark/compare.py` remains for
a future valid run.

**Open:** owner decisions (PR and merge to `main`, B3 task source, pinned
model, board authorisation); research risk
`planner_spec_error_shared_by_oracle_and_rtl` (ROADMAP V1); Codex's parked
November 13 candidate-export stage in
`C:/Users/<user>/Documents/Codex/2026-10-15/hey/work/nov13-candidate-bundle-stage`.

**Environment:** ROADMAP section 3. Keep the machine awake; renew the lease
with `python scripts/lease_keeper.py --token-file <private file>`.
