# Current project checkpoint

Updated 2026-10-20 (America/New_York). Reconcile these notes with Git,
coordination state and actual processes. Notes are not execution evidence.

## Workspace and publication

- Canonical checkout: C:/Users/prince.baah/Downloads/autortl-work.
- Preserve the separate preexisting Downloads/autortl copy.
- Remote: https://github.com/Baah134/autortl
- Tested runtime source: **8098466** (807 regression tests; proof-retention and
  duplicate-definition guards). Streaming build03 was measured atafcc080;
  generated encoder at978c742; generated counter at8b6a162. Each archive records
  its own source; do not assign all measurements to the latest commit.
- Verified integration: main and codex/contract-context both reached
  **a113ca192085bd8406f734f66891a69e35216a99**, containing tested source8098466
  and the complete campaign06 archive. Later continuity-only commits may extend
  it. Inspect actual heads before editing.
- Paused MCP work remains in its original stash. Command-line Vivado is active.

## Standing user decisions

The harness is the product. Designs are experiments that improve verification,
feedback, reliability and efficiency. Weaker-model reliability is a research
objective, not a demonstrated result. Review features periodically for evidence
to keep, improve, simplify or remove them.

Study relevant primary research before substantial changes. docs/RESEARCH.md
records ten source groups, current fit, adoption triggers and test criteria.
Add a mechanism only for a concrete need after comparing a simpler alternative.
No new framework, memory service or provider was installed for the review.

The user authorizes tests, bounded subagents, substantive GitHub pushes and
incremental main integration. One coordinator and exclusive file scopes are
required through scripts/session.py. Checkpoints retain ownership; a handoff
releases it only when actually switching or ending. Read AGENTS/START_HERE and
actual Git state before taking over. Development coordinators may differ;
runtime model roles currently use the existing Codex CLI login.

README is the concise public overview. Agent continuity belongs here and in
START_HERE, AGENTS and the progress log. Preserve unsuccessful attempts and
honest CV evidence. Never modify tests/contracts to publish a gain.

## Completed continuation: generated designs and final campaign

Runtime **8098466** passed **807tests in137.16seconds**. Fresh fulltier0 campaign06
completed2/2,streak1,held=false. Both entries match all53committed runtime file
identities at completion. No higher held tier and no controlled weaker-model claim.

- Counter8 build02 at8b6a162: golden repair;6LUT/8FF retained; independent700-cycleTB.
- Encoder8 build01 at978c742: accepted6to5LUT,4FF; setup0.531/hold0.156ns;
  exhaustive independent saved-winner test passed.
- Two-entry streaming03 atafcc080: combined generated+independent verification,
  **15LUT/19FF,setup0.302/hold0.138ns**;5calls,384.843chargedtoolseconds.
  Baseline retained; candidate equal-area and duplicate companion definition.
  Independent893-cycle saved-winner+child check passed. DONE replay42identities
  unchanged. Earlier qualification and battery-budget failures remain archived.
- Final guards: journal restores raw assertion/miss proof; DONE hashes reports
  and raw proof. Duplicate compiler diagnostics VRFC10-3609/Synth8-9873 reject
  DESIGN even exit0; nonzero infrastructure classification keeps precedence.
  Exact bad candidate failed before elaboration. Focus43/24 tests and peer review.
- Fresh06 counter: accepted **55to31LUT (43.64%)**,37FF,setup0.126/hold0.026ns;
 9/9 final checks. Baseline timing0.494/0.113ns; positive margins decreased.
  3calls,443.859chargedtoolseconds. Actual DONE replay76identities unchanged.
- Fresh06 mux: baseline8LUT/8FF retained,setup0.579/hold0.052ns;3calls,
  427.438chargedtoolseconds; equal-area candidate correctly rejected.
- Archives: generated-streaming, qualification-proof, contract-campaign-06.
  All manifests verified; original paths are provenance, not portable commands.
- Vendor queue finished; no vendor job remains. Temporary keep-awake helper
  confirmed released. No power-plan change was made. Active coordination is a
  saved checkpoint, not a background experiment or scheduled agent switch.
- Main integration verified at a113ca1; full807tests plus freshfulltier0 gates
  passed before the fast-forward.
- Exact next action: inspect Git/processes and acquire/renew coordination, then
  implement the parameterized synchronous FIFO fixture/TB/mutants specified in
  docs/TASKS.md. Qualify real behavioral faults before a generated combined-mode
  build. Reuse the current flow; no new framework/role is justified. Keep runtime
  frozen during each full test or live campaign.

## Earlier completed milestone (historical)

- **655 regression tests passed in 207.64 seconds.** Initial run: 648 passed,
  seven legacy successful-tool mocks lacked new mandatory receipts. Updated
  those fixtures without changing their negative assertions or production gates;
  both logs are retained in evidence/2026-10-20/.
- Durable receipts separate actual process exits from timeout/launch driver
  outcomes. Raw log hashes and latest successful exits are mandatory at both
  baseline and candidate gates. Missing/invalid evidence blocks infrastructure;
  a model ACCEPT cannot override it or score RTL as rejected.
- Simulation input identities are captured before the successful journal commit.
  Replay rejects changed RTL, testbench or ordered companion sources. Physical
  Doctor reuse cites source-identical prior verification and checks its inputs;
  cache and DONE retain receipts, verification manifests and output logs.
- Unannotated optimization latency is explicitly unknown. Typed specs and
  generated TBs require known numeric latency. UTF8 skill decoding is explicit.
- Curriculum cohort identity includes frozen implementation/Python/tool evidence
  and governance code. Missing/mixed identity cannot qualify. CLI model identity
  remains unobserved, so no controlled model-strength claim follows.

## Fresh campaign05: complete

Local: logs/contract-campaign-05/tier0_vm_jufi9.
Portable: evidence/2026-10-20/contract-campaign-05/ (203 verified files).

**2/2 passed; one accepted improvement; runtime-bound streak 1, held=false.**

- Counter: accepted **55 to 53 LUTs (3.6%)**, 37 FFs, setup slack 0.456 ns,
  hold slack 0.282 ns. Independent frozen TB, actual exits, routed reports,
  machine evidence gate and final review (8/8 PASS) passed. Three model calls;
  486.673 reported charged tool seconds. Baseline setup slack was 0.494 ns;
  area improved, while setup slack decreased and remained positive.
- Mux: candidate remained at 8 LUTs and was correctly rejected for no objective
  gain. Verified baseline retained: 8 LUTs, 8 FFs, setup 0.579 ns, hold 0.052 ns.
  Three model calls; 381.297 reported charged tool seconds.
- Actual CLI DONE replay returned the accepted counter winner with unchanged
  budget/summary/winner hashes and no new model or tool calls. This covers
  completed-run reuse, not in-flight hard-kill recovery.
- Vivado 2025.2, xc7a35tcpg236-1, 10 ns and ideal zero minimum/maximum I/O delays.
  One iteration/candidate; 16 calls, 12 tool minutes, 18 wall minutes per design;
  one infrastructure retry. All campaign05 jobs have finished.

Earlier original campaigns remain separate: 01 0/2 (later unchanged-code
recovery), 02 0/2 (negotiation/quota), 03 1/2 (Windows persistence), and 04 2/2
(no promotion: missing exit proof and no mux gain). Campaign04's historical
qualification cannot count toward the new runtime-bound streak. No held tier.

## Earlier coverage plan (historical; current actions above)

1. Inspect remote heads and confirm this source/evidence integration. Claim or
   renew the coordinator and file scopes before edits.
2. Qualify the counter8 and encoder8 trusted top TBs with behavioral mutants.
   Then run typed builds without --tb to exercise generated golden/module-TB
   paths, and independently simulate the saved top plus actual child sources
   against the trusted TB. Exact design names/source lists are in docs/TASKS.md.
   Supplying an independent TB currently bypasses golden generation for a
   single module; do not claim both paths were covered by that one run.
3. Strengthen wrap, disabled-cycle, reset, priority and latency checks. Generated
   counter stimulus alone is too short for 8-bit wrap and has only initial reset.
4. Exercise live cache reuse/invalidation, restart, diversity and complete
   Doctor invocation; then controlled ablations of existing optional features.
5. Test actual process interruption/accounting separately. Persistent storage
   failure or a hard kill can leave tool work beyond the last charged budget;
   external execution and budget charging are not one transaction.
6. Run an actually available, identified weaker model with frozen tasks/budgets
   before claiming model robustness. Three matching full qualifying cohorts
   are required for a held tier. Increase design complexity with verification.

## Local tools

Python: C:/Users/prince.baah/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
Test deps: C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work/review_deps
Vivado binaries: C:/AMDDesignTools/2025.2/Vivado/bin.

Use explicit workdir, PYTHONDONTWRITEBYTECODE=1, test PYTHONPATH and a fresh
writable pytest basetemp. Keep one Vivado queue. Downloads writes, Git metadata/
network and vendor launchers may need the already-authorized execution profile.
Never edit runtime files during a frozen test/campaign or resume across changed
implementation. Check actual process state before starting the next run.
