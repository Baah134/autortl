# Current AutoRTL checkpoint

Updated October 29, 2026 (America/New_York). Verify files, Git, ownership and
actual jobs before acting. Canonical checkout: Downloads/autortl-work. Preserve
the separate Downloads/autortl copy. User choice: command-line Vivado.

## Latest - October 29 (Claude Code): tier1 started; model-portability branch

The user's direction: the harness's roles do the design work; Claude
supervises, reads the roles' logs and improves the harness and roles so any
LLM can work in it. The user overrode CLAUDE.md's Codex-only rule. The
working plan is docs/PLAN_24H.md (on claude/model-portability until merged).

- **tier1-campaign-01** (old 232-file identity): 3/4, not qualifying
  (evidence/2026-10-29/tier1-campaign-01). counter8 and encoder8 (6 -> 5
  LUT) passed; pwm passed with no gain; debouncer ended at spec lint.
- **Branch claude/model-portability** (worktree Downloads/autortl-portability):
  six taxonomy entries, each committed before its fix: fence tags other
  models write, golden fence tags, evaluator verdict forms, a run-pinned
  model (`--model`, recorded in the cohort), planner spec repair with the
  structural rules in the prompt, and a mechanical default timescale for the
  verified seed copy. Also tools/role_report.py (per-role calls, verdicts,
  repairs) and a reworked README. Not merged yet.
- Codex CLI accepts other models on this login (gpt-5.6-luna, gpt-6.1-sol
  tested). Gemini CLI is refused (free tier unsupported); the Claude CLI is
  not logged in for headless use.
- Run benches one at a time: run_tier rewrites the whole history, so a
  concurrent bench drops a record (append-safe fix in progress).

## October 29 (Claude Code): tier0 held on the changed harness

- **Tier0 is held**, for the first time in the project's history.
  campaign15, 16 and 17 all ran `tools/tier0_gate.py` on the same 232-file
  freeze (`a611829c…`, cohort `78b298ad…`) and each passed 2/2 with 1,461
  tests and every prefix unchanged. The streak reached 3, and the last
  curriculum record has `held: true` (evidence/2026-10-29/contract-campaign-16
  and -17). Counter: 53, 31 and 53 LUTs from a 55-LUT baseline; mux4 stayed
  at 8. campaign16's 31-LUT winner takes overflow from the increment's
  carry-out.
- A held cohort now protects its passing entries: a later run on this
  identity that fails counter or mux4 is a held regression and does not
  qualify. Any frozen-source change starts a new cohort.
- The golden worker's fixed budget is documented in docs/DESIGN.md (item 3),
  with measured UART limits (2,500 to 3,000 cycles per example).

## October 29 (Claude Code): harness-built design on the board; two harness fixes

The user gave Claude full authority over the repo, including running the
harness.

- **Harness-built UART TX on the Basys 3.** `run.py build` on
  hardware/basys3/harness_built/uart_tx/design_spec.json produced a UART TX
  (run 03: 34 to 22 LUTs, 14 calls, 9.4 min). The unedited winner drives the
  board's TX pin and echoed 100,000 of 100,000 bytes. Evidence:
  evidence/2026-10-29/harness-uart-tx-01, including the two failed runs.
- **Harness fix 1 (bc959cc), stale_companion_masks_inlined_candidate.** A
  candidate that stops instantiating a companion the trusted testbench
  instantiates is now rejected (autortl/companions.py). Run 04 on the fixed
  harness kept the child and its parameter: 39/28, the same board results
  (evidence/2026-10-29/harness-uart-tx-02).
- **Harness fix 2 (e062271), checkpoint_replace_denied.** A locked
  checkpoint raises CheckpointLockedError, and run.py reports
  `infra_blocked` with exit code 3.
- **The merge gate passed, and main is integrated.** campaign15
  (`tools/tier0_gate.py`: campaign14's budgets on the fresh 232-file
  freeze) passed 2/2, with 1,461 tests and every prefix unchanged
  (evidence/2026-10-29/contract-campaign-15). main was fast-forwarded to
  30d16a4, the same commit as codex/contract-context, and CI is green on both.
  campaign14 is superseded and must not be launched: its freeze is stale.
- **The v2 UART spec (shortened stop bit) streamed 1,000,000 of 1,000,000
  bytes** at line rate on the board, with a 24-LUT harness winner
  (evidence/2026-10-29/harness-uart-tx-v2-01).
- The Fmax study of all six winners is archived
  (evidence/2026-10-29/fmax-characterization-01).
- Next options: (done Oct 29: tests/test_module_latency_gates.py now matches its blob, LF only),
  since every freeze needs a reconstruct rule for it. Decide the
  io_dominated_timing_metric question in docs/TASKS.md. (Holding tier0 is
  done: campaign16 and 17.)
- Never `tail -F` a live run file on Windows; it crashed run 02.

## October 28, session 3 (Claude Code): repository-wide evidence audit

- **`tools/evidence_audit.py`** checks every SHA-256 claim in every claim
  file under evidence/ against committed blobs (PUBLICATION.md step 5, which
  had been applied to seven archives only). Claim files are the manifests plus
  source freezes, launch-source lists, launch plans' runtime_source and
  tested-source identities; deleting a claim file fails. CI's `evidence` job
  runs it with full history on every push. 45 tests in `tools/tests` use fixtures of each
  real layout. Run `--worktree` before committing a new archive. Run records
  (journals, state, results) are out of scope and counted in each report.
- At fef63d4 it finds **837 failing claims** of 27,073. 532 never-copied
  archive files (XSIM .pb/.jou, xsim.dir logs, reports) were restored
  byte-exact from their own runs under logs/. The 8 tested bitstreams are
  archived in basys3-bitstreams-01. 27 tested sources that were never
  committed are proven from archived source snapshots (21) or copies
  recovered from Codex staging folders (6). Everything else is
  in `tools/evidence_exceptions.json` (schema 2): each claim is pinned by
  digest and failure status, and is either proven by readable bytes or
  recorded as a loss. That file is generated by
  evidence-integrity-01/make_exceptions.py; edit the rules there, not the
  JSON. The full account is in evidence/2026-10-28/evidence-integrity-01.
  docs/PUBLICATION.md has six new taxonomy entries.
- Two independent review rounds (798, then 817 failures) found coverage,
  silent-pass and exception-matching gaps; eebedce closes them.
- **For Codex:** a source freeze of a Windows working copy is checked as a
  CRLF checkout of a committed blob. tests/test_module_latency_gates.py has
  one CRLF line in the working copy, so every freeze needs a `reconstruct`
  rule for it. Normalizing that file's line endings and committing it would
  stop the repeats. A new freeze, manifest or lost archive file now fails CI
  until it verifies or is classified in make_exceptions.py.
- Board suite: `python -m hwsuite program|hw --design NAME --bit FILE` tests
  an archived bitstream from a fresh clone, with no synthesis. `program`
  records what it loaded (build/programmed.json), and `hw` reports that. All
  six winners were replayed from the archive on the board, and every result
  reproduced exactly (basys3-bitstream-replay-01).
- No frozen source, runtime or run result changed. Campaign14 is still the
  next gate and still Codex's.

## October 28, session 2 (Claude Code): Basys 3 hardware and agent mailbox

Claude Code claimed the released lease normally (no takeover) and checkpoints
there; query `python scripts/session.py status` for the live owner. Read your
messages first: `python coordination/mail.py inbox --for codex`.

Completed and verified this session:

- **First physical-hardware evidence.** A hand-written UART echo
  (`hardware/basys3/uart_echo`) runs on the user's Basys 3. Version 01 passed
  chunked tests but lost bytes under a line-rate stream (first loss at byte
  9,696), as an independent review predicted; evidence/2026-10-28/basys3-uart-echo-01.
  Version 02 shortens the transmitted stop bit by 1/16 bit, waits for the
  line to go high after a frame error (break handling), and adds overflow and
  frame-error LEDs. It streamed 1,000,000 bytes at line rate with 0 loss; the
  wrong-baud control failed as required. Each fix has a fault check that fails
  when that fix is reverted. Build: 0 warnings, WNS +4.529 / WHS +0.106 ns,
  77 LUT / 94 FF; evidence/2026-10-28/basys3-uart-echo-02.
  The board's UART is COM10 and its JTAG target is Digilent 210183B31D15A.
- **Agent mailbox.** `coordination/mail.py` with `coordination/messages.jsonl`
  for questions, requests and blockers between agents (21 tests in
  `coordination/test_mail.py` with fixture logs). See coordination/README.md and DECISIONS.
- Arrival/departure steps in AGENTS, AGENT_HANDOFF and START_HERE now include
  the inbox.

- **Campaign13 assessed and archived** (evidence/2026-10-28/campaign13-interrupted-01).
  Only `counter` started; it stopped during iteration 1 synthesis after 2 model
  calls, with no completion receipt or history record. It is not a pass and is
  not resumed. The 230 frozen identities still match its prelaunch record.
  **Next gate: campaign14**, a fresh full tier0 run with the original budgets.
  `work/run_campaign14.py` differs from run_campaign13.py only in its output
  paths. It is not launched yet: the session's keep-awake request was denied,
  and a PC sleeping mid-run is the likely cause of campaign13's interruption.
  The user decides how to proceed. Launch with the Codex 3.12 Python,
  PYTHONPATH=work/review_deps and AUTORTL_CODEX_BIN set to the installed Codex
  CLI (codex is not on PATH in non-Codex shells).
- README rewritten as a portfolio front page (0d468ff, development only; main
  still shows the old README until the gates allow integration).
- **Harness FIR on hardware.** `hardware/basys3/fir4_on_board` runs the FIR01
  winner, byte-identical (SHA-256 55e3c7d0…), behind a hand-written UART
  shell. On the board, 100,000 samples matched a Python model with 0
  mismatches and 4 break-restarts, and a wrong-coefficient model failed as
  required. In simulation, faulted copies (coefficient, missing reset) fail.
  Build: 0 warnings, WNS +2.718 ns. Evidence: evidence/2026-10-28/basys3-fir4-01.
  No harness source was touched; it is a board-level replay of an existing result.
- Campaign14 is left for Codex (user decision); see mailbox #3.
- **Every harness winner on hardware** (`hardware/basys3/harness_winners`,
  evidence/2026-10-28/basys3-harness-winners-01). One generic tested shell with
  thin adapters runs all six archived winners, unedited and hash-checked
  against run state: FIR, elastic dot4, pipelined dot4, divider, packet FIFO
  and sync FIFO.
  - Each design: sim of 1,200 transactions with a restart and coverage gates,
    an injected fault that must fail, 0 build warnings, positive timing,
    50,000 hardware transactions with 0 mismatches and 10 restarts, and a
    wrong-model control that fails.
  - Independent Python models are written from the frozen specs.
  - Board builds reproduce the harness's resource measurements. The divider's
    8-FF gap is standalone `opt_design` replicas
    (evidence/2026-10-28/divider-ff-replica-analysis-01).
  - Run: `python -m hwsuite all` from that folder. It needs the system Python,
    which has pyserial; tests need pytest.
- **CI** (`.github/workflows/tests.yml`): the full harness suite on Windows,
  plus the mailbox and board-suite tests on Windows and Ubuntu. A clean
  fresh-clone run of the harness suite passed 1,450 tests in 320 s with no
  Vivado and no ignored directories.
  - On the first GitHub run the harness job passed, but the tooling jobs
    failed: `*.log` in .gitignore had kept three board-suite fixtures out of
    the commit. Fixed in 96b250a.
  - All jobs have been green since 2d8ee81. Actions are at checkout@v7 and
    setup-python@v7 (no Node.js 20 warning).
- Removed the stray 0-byte root `xelab.pb` (from 387fe0e; nothing referenced
  it, and it is outside the frozen sets). Root `/*.pb` and `/xsim.dir/` are
  now ignored.
- `docs/WALKTHROUGH.md`: a guided code tour for the user, with 66 file:line
  references checked against the code. Re-check those references after any
  change to `fsm.py`, `bestofn.py`, `tbgen.py` or `vivado.py`, since line
  numbers will shift.

State at Claude's handoff: development `codex/contract-context` at the
commit that adds this line. CI is green; the working tree is clean. No
Vivado or board job is running. The board holds the sync_fifo shell
bitstream (volatile). `main` is unchanged at 185dadc. Codex's next action
is still campaign14 (mailbox #3); read messages #1-#6 first.

Deliberately untouched: every file in the frozen 230- and 201-file identity
sets (autortl/, llm/, tests/, curriculum/, scripts/, data/, .claude/, run.py),
and campaign13 and its output. The previously pending Codex docs/TARGETS.md and
docs/TASKS.md edits and the FIR02 archive (642 files verified against its
manifest) were committed unchanged in b0e6c61. The Codex next action below is
still open.

User direction recorded this session: the project's goal is a strong portfolio
piece for FPGA graduate roles. The agreed flagship is a harness-built design
running on the Basys 3 with real pin constraints and a hardware-in-the-loop
check against the Python reference. A fixed-point CORDIC/exponential unit is
the candidate block; it must be a fresh design unless the user's research
advisor approves reuse. Harness support needs a checked-in board XDC (never
model-generated), a bitstream step and an optional programming step. These
touch frozen source, so start only after campaign13 has a recovery decision.

Tooling note: the default `python` here is 3.14 without pytest. Tests ran with
`C:/Users/prince.baah/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`
and `PYTHONPATH=C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work/review_deps`.

## Earlier October 28 checkpoint (Codex): sequential-agent accommodation

The user clarified that Codex and Claude Code take turns. No concurrent-worker
runtime or schema was implemented. The existing transactional coordinator lease,
task scopes, checkpoint and handoff commands remain the coordination mechanism.
Follow the new arrival/departure checklist in docs/AGENT_HANDOFF.md. Existing
coordination tests passed15/15 (2.36s); all201 checked implementation/design
input identities were unchanged. Evidence: evidence/2026-10-28/agent-coexistence.
This documentation milestone is published only to development; the active
coordinator releases its lease after publication. Query live status to confirm.

At the inspection, no Claude Code, Python, Vivado or XSIM process was visible
in the local process-name check. This is a point-in-time check, not a guarantee
that another agent cannot start later. Query live ownership before editing.
The October26 Codex lease had expired; a documentation-only coordinator claimed
it normally without takeover. The current lease state must come from session.py.

Development HEAD before this documentation change: cbab6cf. Local main:185dadc.
No runtime implementation, test, hardware fixture or previous archive was edited.
Unrelated pending docs/TARGETS.md and docs/TASKS.md changes and the untracked
evidence/2026-10-26/generated-signed-fir4-attempt-02 archive are preserved.

Important correction to the historical snapshot below: FIR02 is completed,
not active64015. Its launch receipt reports exit0, source unchanged and
1404.719s CLI wall time. Its independent evidence archive reports84LUT/69FF,
setup+.147ns/hold+.071ns,800cycles,14calls. Keep its separate original52LUT result.
Campaign13 has only the counter run; the last events show synthesis RUNNING,
but no completion/launch-result receipt was found and no vendor process was
visible. Treat this campaign as interrupted/unverified. Do not claim tier0 passed,
merge the changed runtime to main, rerun into its old directory, or resume it
without preserving/reconciling its original inputs, budgets and tool receipts.

Next engineering action: inspect campaign13's complete saved state and receipts,
preserve the interrupted attempt, then choose only a supported source-bound
recovery or a separately budgeted fresh gate. Do not run the archive helper that
requires a passing complete campaign against this incomplete attempt. The
provisional MAC12 fixture has not started; finish runtime gates first.

## Historical October26 checkpoint (superseded job status)

The following records preserve the earlier checkpoint; its ACTIVE process IDs
and exact-next-action list are historical. Use the current section above and
actual files/processes rather than treating those jobs as still running.

## Published milestone

GitHub main and development were verified at
185dadc119ebf7e8755c7257dc16d3e6576fd087. Local main was fast-forwarded without
checking out or changing working files. All 1,155 committed archive blobs match
three manifests. This is the original 227-file FIR milestone, before the local
verification correction below. The published harness runtime matches be60de7.

- Full regression: 1,429 passed in 558.54 seconds, all 227 identities unchanged.
- Independent FIR admission: control plus 27 compiling behavioral faults, 28/28.
- Generated signed FIR: 78 to 52 LUTs, 66 to 67 FFs, no DSPs; setup -0.327 to
  +0.169 ns, hold +0.106 ns; reported estimated power unchanged at 0.088 W.
- First feasible design used 80 LUTs. Final result used 12 model calls,
  1,190.343 charged tool seconds and 1,429.016 CLI wall seconds.
- Exact saved top and frozen child independently passed 800 cycles. Actual
  DONE reuse succeeded; six restored tamper probes failed as required. All
  454 protected identities, budget, router statistics and file set stayed intact.
- The original run and its 610-file archive are never resumed or regraded after
  runtime changes. This does not prove arbitrary in-flight crash or formal safety.

## Current local work: verification correction; full regression active

Frozen original generated-grader audit measured 18/27 faults detected, nine
missed, zero ungraded. Independent verification detected all 27. That audit is
archived with 287 files before correction; original run/budget/statistics intact.

The correction uses existing mechanisms: six alternating signed boundary
payloads, legal invalid bubbles/noise, and wholly off-edge pulses for synchronous
reset contracts. Producer hold uses the previous rising-edge handshake. Oracle,
schema, roles, budgets and severity/verdict policy are unchanged. Taxonomy and
acceptance criteria were recorded before implementation.

- Signed-only proof: same original generated oracle/reference/truncation fault;
  old fault passed, corrected grader emitted five assertions, both controls
  passed. 104 to 110 payloads; original prefix/random inputs preserved; expected
  range reaches -2169 and 2166. Intermediate 228-file snapshot archived (266 files).
- Driver proof: all five nominal controls passed coverage, including zero-latency,
  busy operation, 16-cycle input blocking, renamed active-low and async reset.
  A deliberately bad producer driver triggered nine monitor errors. Those six
  probes are separate from the RTL fault denominator.
- Full corrected audit: 22/27 detected, five missed, zero ungraded; same old
  oracle/reference/faults and byte-identical signed-only payload/expected arrays.
  No models or synthesis; 415.375 diagnostic wall seconds. Archive has 597 files
  and the exact staged 230-file source. Independent review found no blocker.
- Remaining faults concern occupied reset retention and FIR-specific port values
  during asserted reset. Generic ResetSpec lacks pending flush/preserve policy;
  the independent contract checker continues to cover these properties.
- Pure staged focus: 117 passed in 6.83 seconds; original four failed/six passed
  preserved. Signed-only focus 107 passed; its original seven/four retained.

Canonical source now exactly matches the vendor-tested 230-file stage. Only
autortl/tbgen.py and data/taxonomy.yaml differ in the runtime implementation;
three new test/helper files and a fixture README correction are also local.
No further source, test or fixture edits during frozen experiments.

Full regression 56345 completed: **1450 passed in 457.63 seconds**.
All 230 identities stayed unchanged. Archive: evidence/2026-10-26/
fir4-coverage-tests-01. No test/vendor/model job currently active. Tested runtime cbab6cf2a69070a0f3f4f19f78f7eab69453329c is pushed to
development; all 2,556 committed archive blobs verified. NEW FIRbuild02 ACTIVE
64015, original admitted spec/TB and original fixed budgets. Source230 stays
frozen. Fullsuite56345 completed; do not edit source during build02/campaign13.

Temporary system-awake helper: 96281, watching work/fir4-coverage-awake.flag,
bounded 120 minutes since about 09:41. Previous 6908 released and completed.
Remove the current flag and verify helper exit when the queue ends; no permanent
power settings changed.

## Exact next actions

1. Finish 56345; inspect fir4-coverage-full-result-01.json. If passing, run
   work/archive_fir4_coverage_tests01.py; preserve any failure before edits.
2. Publish the reviewed tested runtime to development. Verify exact source230
   and committed archive blobs. Main remains the completed original milestone
   until the changed runtime's remaining gates pass.
3. Launch work/run_signed_fir4_build02.py in a fresh output directory. Same
   admitted spec/TB; N=1, at most 3 iterations, 16 calls, 25 tool / 35 wall minutes,
   one infrastructure retry, no qualification-reference seed. Do not modify or
   resume original01 under this runtime. Preserve all new outcomes and costs.
4. On actual DONE, independently verify exact winner/child and restored probes,
   then archive02 BEFORE another model job (router record slicing is bound).
5. Run work/run_campaign13.py: fresh FULL tier0 runtime gate, original budgets.
   This is a required regression, not a new counter design objective. No higher
   tier is held. Archive actual history/cohort and source verification.
6. Integrate main only after these gates; verify remote heads and committed
   manifest blob bytes. Update README from actual results and refresh shared
   memory. Release temporary awake request when the owned queue ends.

## Evidence and ownership

Workspace: C:/Users/prince.baah/Documents/Codex/2026-10-15/hey. Helpers in work/;
raw outputs in outputs/. Canonical evidence/2026-10-26 contains generated FIR01,
original generated-grader audit, signed-boundary comparison and driver comparison.
Independent admission remains evidence/2026-10-25/signed-fir4-admission-attempt-01.
Git and PROGRESS preserve prior FIFO/divider/dot-product milestones.

Coordinator: Codex / signed FIR4 Oct26, eight-hour lease. Root owns canonical
fixture, notes/evidence and signed-scoreboard-corners scopes. Isolated stages:
fir4-signed-corners-stage and fir4-driver-stage; do not rewrite their frozen proof.
One coordinator and one vendor queue. No automatic scheduling/provider failover.

Target: xc7a35tcpg236-1, 100 MHz, ideal zero min/max I/O; no board deployment.
Prior runtime gate was campaign12, 2/2, new-cohort streak one, held false.
No controlled weak-model or product-superiority claim is made.

Next-design feasibility: raw4x4matrix238IOBs exceeds106 available. Provisional
MAC12 (79IOBs, signed25 result, age13) is recorded in TASKS; no implementation
started. Freeze and admit its full contract only after currentruntime gates.
