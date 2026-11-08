# AutoRTL current checkpoint

## Current — November 8, 2026: finite GF/AES boundary

**Staged proposal, not a new execution receipt.** Prepared from a read-only
snapshot at approximately 21:52 UTC (16:52 America/New_York). Before integrating
this replacement after AES04, the coordinator must replace the two pending
records below from actual receipts and update this timestamp. Do not publish
placeholders as a completed handoff.

| Record | Verified snapshot / required completion |
|---|---|
| Checkout | `C:/Users/prince.baah/Downloads/autortl-work`; preserve separate `Downloads/autortl` |
| Branch / source | Documented development `codex/contract-context`; last published pre-GF source `defd87f`. Worker could not independently query Git; coordinator must record actual HEAD and remote verification |
| Ownership / jobs | Coordinator owns canonical integration and one vendor queue. Last coordinator-recorded regression PID 23756, pytest 15792, supervisor 23364; these are recovery pointers, not proof of liveness |
| Pipeline snapshot | Workspace `work/nov8-gf-pipeline-status.json` said `waiting_for_existing_tests`; full-test `results.json` was absent when read. No new full-regression success inferred |
| GF publication | **[PENDING: actual commit, both suite outcomes/skips, frozen-input count, audit, archive verification and remote receipt from `work/nov8-gf-publication.json`]** |
| AES04 | **[PENDING: actual child status/exit, module outcomes, calls/time, source drift and archive verification; or exact not-launched/blocking reason]** |
| Main / board | Last documented main `ca61dbc`; no main update authorized before final release gate. Connected Basys 3 remains outside this stage: no hardware access |

Workspace prefix for local `work/` paths:
`C:/Users/prince.baah/Documents/Codex/2026-10-15/hey`.
Repository-relative `logs/` and `evidence/` paths are in the canonical checkout.
Workspace files are local diagnostics; published immutable evidence is the
durable fresh-clone record.

### Evidence needed to close this checkpoint

- Software: workspace `work/nov8-gf-full-tests-01/results.json`,
  `source-freeze.json`, `harness-tests.txt` and `tooling-tests.txt`.
  Both actual exits must pass with unchanged selected inputs; partial progress
  output is not a result. Publication supervisor: `work/nov8_gf_pipeline.py`;
  status: `work/nov8-gf-pipeline-status.json`.
- GF proposal: `work/nov8-gf-guidance-stage/receipt-v2.json` and
  `proposal-v2.patch`; final staged eight affected tests passed. The earlier
  112-test focused result belongs to V1; do not relabel it as a full V2 suite.
  Production change only clarifies primitive-generator coverage and inverse
  identities; roles, attempts, sandbox and budgets remain unchanged.
- Publication: `work/nov8-gf-publication.json`, `work/nov8-gf-audit.json`,
  `work/nov8-gf-audit.txt`; intended repository archive
  `evidence/2026-11-08/gf-guidance-01`. Verify actual committed bytes and remote
  head, not merely planned paths or a successful wrapper exit.
- AES04: `logs/explore-aes-20261108-04-launch.json`, `-launch-result.json`,
  `-source-freeze.json`, `.console.txt`, and
  `logs/explore-aes-20261108-04/aes128_core_build/run_summary.json`.
  Intended archive: `evidence/2026-11-08/explore-aes-20261108-04`.
  Inspect module reports and raw verdicts before reporting design success;
  this exploration does not itself establish a curriculum hold.

### Exact next actions and stop rules

1. On arrival or compaction, query compact live coordinator/checkpoint state,
   Git and actual jobs. Read pipeline/result files above. Do not relaunch the
   supervisor, full regression or AES04 while their ownership/outcome is
   unresolved. Claim exact scopes only through `scripts/session.py`; follow
   `docs/AGENT_HANDOFF.md` if ownership expired or the prior session stopped.
2. The existing supervisor alone may publish after two successful unchanged-input
   receipts, audit and verify the publication, then launch **at most one fresh
   AES04** through `work/nov8_aes_explore04.py`. Retain the original contract,
   model configuration, budgets, three oracle attempts, qualifiers and tool
   boundary; no lower-tier reholds. The wrapper binds published HEAD, frozen
   sources and qualified CLI digest. A mismatch or changed CLI is a stop and
   requalification decision, never permission to remove a guard.
3. If tests/publication fail or supervision ends, preserve the actual failure
   and reconcile source, budgets, processes and receipts before any recovery.
   Do not rerun into an existing attempt, resume spent work on new sources or
   assume an absent receipt means no job started. Do not terminate unfamiliar
   processes. No automatic retry or additional AES campaign is authorized here.
4. Archive and verify every AES04 outcome, including quota/interruption/failure,
   with costs and source drift. **After AES04, stop AES-specific prompt tuning
   regardless of outcome. No AES05.** Move to benchmark/release work; success
   does not justify more AES tuning and failure is not a reason to expand budgets.
5. After the pending records are resolved, integrate this concise memory cleanup
   as documentation only, append a dated `docs/PROGRESS.md` entry, audit and
   publish meaningful tested progress to development. Preserve the original
   documents in an immutable reviewed archive; do not erase their evidence.

### Verified baseline and limits

Published pre-GF `defd87f` recorded 2,087 harness and 323 tooling passes, one
native Windows symlink-privilege skip and 342 unchanged selected inputs.
AES03 recovered `aes_ctrl` through oracle, RTL/unit and mutation qualification;
`aes_round` then failed oracle construction (two setup-budget failures, one
wrong-output program). It did not establish full AES, top/PPA, curriculum or
board success. Its 116-entry archive is
`evidence/2026-11-08/explore-aes-20261108-03`; diagnosis is in
`docs/CASE_STUDY_ORACLE_CONTEXT.md` and `evidence/2026-11-08/aes03-review-01`.

Recorded older tier holds remain tied to their original runtime; tier 3 was
4/5 with UART/FIFO failure, and tier 6 was 2/3, not held. The quota-blocked
signoff4-t6-02 has no design verdict and must not be resumed or counted as a
pass. Old mailbox campaign14/merge instructions are superseded by later user
decisions and the final-release freeze. Do not execute them on arrival.

No scored public benchmark or superiority claim is established. Follow
`docs/ACTION_PLAN.md`: first a disjoint adapter pilot and a preregistered pinned
dataset/task roster; then 30–50 tasks, three trials and three arms (single call,
bounded ablation, full harness) with the same independent final grader and
honest budgets, false acceptance, cost and uncertainty reporting. The proposed
40-task/six-pilot study is not yet a registered or executed result. Keep
functional accuracy distinct from routed PPA; tools-enabled agent comparison
needs its own baseline, and public tasks do not exclude training contamination.

Do not repeatedly re-hold completed tiers during development. Freeze the final
release identity and complete its sign-off/re-hold plus publication/audit gate
before integrating main. Keep board/OOC constraints distinct and historical
hardware evidence separate from this software/AES stage. No board command is
authorized by this checkpoint.

Historical engineering and CV evidence belongs in append-only `docs/PROGRESS.md`,
Git history and immutable `evidence/` archives, not additional current sections.
Coordination/recovery rules remain in `AGENTS.md` and `docs/AGENT_HANDOFF.md`;
the README remains the public project overview. Durable files aid recovery but
do not schedule execution, guarantee resumption or switch runtime providers.
