# AutoRTL current checkpoint

One current section only. History lives in `docs/PROGRESS.md` and Git. The plan
of record is `docs/ROADMAP.md`; the review behind it is
`docs/REVIEW_2026-11-15.md`.

## Current — November 26, 2026: release PR open; re-hold running

Coordinator: Claude. Branch `codex/contract-context`, pushed; release PR
Baah134/autortl#1 to `main` is open, CI green, mergeable, awaiting the owner's
merge. `main` frozen at `ca61dbc`.

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
`evidence/2026-11-26/flash-03-results`. Its pinned worktree is removed.

**Merged:** `c6-dedupe` (with bench-fixes) into this branch (`1d841a53e`).
Suites green on the merge: 2,384 harness, 325 tooling, ruff clean, evidence
audit PASS. `docs/WALKTHROUGH.md` line references replaced by symbol names.

**Release re-hold** (curriculum tiers re-held once on the release runtime,
`1c341f798`, by `tools/signoff.py` through a driver that counts only verdict
campaigns toward the cap of 6): tiers 0 and 1 held. Tier 2 campaign 2 scored
2/4 because two designs failed xelab with [XSIM 43-3409]: in that worktree
xelab's object path was exactly 260 characters (Windows MAX_PATH). The pass
continues on the same commit from a short-path worktree (`C:/Users/<user>/ar`;
a `subst` drive is resolved back to the long path); t2-02 stays in the record,
tier 2's streak restarts. Campaigns t2-03 and t2-04 gave no verdict (Codex
quota); t2-04 confirmed the short path builds. Tiers 2 to 5 remain. Evidence
is committed on `claude/release-rehold` when the pass ends.

**v1.1 integration branch** `claude/v1.1-integration` (pushed, no PR; lands
after the release): post-release fixes (signoff verdict-only cap; dispute rule
counts only attempts that ran; latency-0 example timing in the planner prompt;
43-3409 as infrastructure and a MAX_PATH check before xelab), the opt-in
Icarus grader compile check, the request cross-check (off by default), the
benchmark case study and the B3 PPA tooling with its DRAFT registration.
Suites green on it: 2,467 harness, 329 tooling, ruff, evidence audit PASS.

**Exact next action:** the owner merges PR #1; then tag `v1.0.0` on the merge
commit (preferably once the re-hold has held every tier) and publish the notes
from `docs/RELEASE.md`; then open the PR for `claude/v1.1-integration`. Optional next work (v1.1): a planner rule
against unstated behaviour, measured on a fresh task set (results on the
final-02 tasks are labelled tuned, `docs/DECISIONS.md` 2026-11-21).
`flash-02` stays withdrawn; a Flash run needs a new registration with Flash-low.

**Open:** owner decisions (merge PR #1, B3 registration freeze: task source and
pinned model, board authorisation); research risk
`planner_spec_error_shared_by_oracle_and_rtl` (ROADMAP V1); Codex's parked
November 13 candidate-export stage in
`C:/Users/<user>/Documents/Codex/2026-10-15/hey/work/nov13-candidate-bundle-stage`.

**Environment:** ROADMAP section 3. Keep the machine awake; renew the lease
with `python scripts/lease_keeper.py --token-file <private file>`.
