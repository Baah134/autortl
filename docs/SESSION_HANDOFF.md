# AutoRTL current checkpoint

One current section only. History lives in `docs/PROGRESS.md` and Git. The plan
of record is `docs/ROADMAP.md`; the review behind it is
`docs/REVIEW_2026-11-15.md`.

## Current — November 21, 2026: final-02 graded; release awaits owner

Coordinator: Claude. Branch `codex/contract-context` (local commits not yet
pushed). `main` frozen at `ca61dbc`; no PR yet.

**final-02 done.** All 360 cells attempted November 21 11:28; graded by
`benchmark.finish`, audit PASS, archived in
`evidence/2026-11-21/final-02-results`. Registered verdict
`single_call_better`: single call 94.1% (111/118), ablation 84.7%, full
harness 86.1% (99/115); C minus A -9.2 pp (95% CI -19.2 to -0.8); C minus B
+0.4 pp (no material difference); 7.4x model calls per pass. False acceptance
9.1% (B), 10.0% (C), flagged. Infrastructure stops 2 / 2 / 5, under the limit.
README row, Known limits, `docs/RESULTS.md`, ROADMAP B1 and the release drafts
carry the verdict.

**Failure review** (taxonomy filed; verdict unchanged): planner misreadings
shared by oracle and RTL (Prob066 reset clearing a history register, Prob139
sampling phase, Prob070 don't-care cover) explain most of the gap
(`planner_spec_error_shared_by_oracle_and_rtl`); Prob131 and Prob153 are
fixed since (bench-fixes); Prob093 and Prob149 references contradict their
prose and fail every arm (`official_reference_contradicts_request`, 5 of C's
11 false acceptances); Prob027 full#2 is a correct design the Icarus grader
rejects for a Vivado attribute (`grader_rejects_vendor_attribute`).

**flash-03 done (November 26):** closed-book Gemini 3.8 Flash-low single call
on the final-02 tasks, registered before any cell (re-frozen once, before any
cell, after the agy CLI update lingered ~100 s after each result; bridge fixed,
`agy_exits_late_after_result`). 103/120 (85.8%, CI 75.8 to 94.2), no
infrastructure stops; paired with Codex arm A -8.3 pp (CI -15.8 to -1.7),
descriptive. Fails Prob066/Prob139 like the harness planner did. Evidence
`evidence/2026-11-26/flash-03-results`. Pinned worktree
`.claude/worktrees/flash03-runtime` can be removed.

**Merged:** `c6-dedupe` (with bench-fixes) into this branch (`1d841a53e`).
Suites green on the merge: 2,384 harness, 325 tooling, ruff clean, evidence
audit PASS. `docs/WALKTHROUGH.md` line references replaced by symbol names.

**Exact next action:** owner approval for RELEASE step 5: push, open the PR
`codex/contract-context` -> `main` (text in `docs/RELEASE.md`), and after CI
and the owner's merge tag `v1.0.0`. Optional next work (v1.1): a planner rule
against unstated behaviour, measured on a fresh task set (results on the
final-02 tasks are labelled tuned, `docs/DECISIONS.md` 2026-11-21).
`flash-02` stays withdrawn; a Flash run needs a new registration with Flash-low.

**Open:** owner decisions (PR and merge to `main`, B3 task source, pinned
model, board authorisation); research risk
`planner_spec_error_shared_by_oracle_and_rtl` (ROADMAP V1); Codex's parked
November 13 candidate-export stage in
`C:/Users/<user>/Documents/Codex/2026-10-15/hey/work/nov13-candidate-bundle-stage`.

**Environment:** ROADMAP section 3. Keep the machine awake; renew the lease
with `python scripts/lease_keeper.py --token-file <private file>`.
