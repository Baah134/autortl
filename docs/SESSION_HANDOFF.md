# Current project checkpoint

Updated 2026-10-20 (America/New_York). Reconcile these notes with Git,
coordination state and actual processes. Notes are not execution evidence.

## Workspace and publication

- Canonical checkout: C:/Users/prince.baah/Downloads/autortl-work.
- Preserve the separate preexisting Downloads/autortl copy.
- Remote: https://github.com/Baah134/autortl
- Tested runtime source: **5d285c0** (71910e5 plus the previously unstaged,
  already-tested conventions file). No runtime bytes changed during campaign05;
  all 54 test/runtime/governance file identities matched.
- Main integrates that runtime and the complete campaign05 evidence. The active
  development branch is codex/contract-context. Inspect actual remote heads and
  Git history before the next edit; later evidence/docs commits extend the
  runtime source commit without changing its tested implementation.
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

## Latest completed milestone

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

## Exact next work

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
