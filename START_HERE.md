# AutoRTL shared project memory

This repository is the shared workspace for every coordinator and its workers.
You can continue without access to the previous provider's conversation.

Canonical checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
GitHub integration branch: `main`. Development branch: `codex/contract-context`.
Verified main/development milestone **185dadc**: generated signed FIR reduced
78 to 52 LUTs and recovered setup timing to +0.169 ns (hold +0.106 ns), with an
independent 800-cycle replay and six restored integrity probes. Full 1,429-test
regression and 28-case independent checker admission passed. All 1,155 newly
published evidence blobs were verified against committed bytes.

Current local work strengthens generated verification: a frozen 27-fault audit
measured 18 detections before correction and 22 after it, with five legal driver
controls and a detected faulty-producer probe. The exact 230-file runtime passed 1,450 tests in 457.63
seconds. Tested development publication is next; fresh FPGA gates remain pending. Read SESSION_HANDOFF
for actual jobs and exact next commands before editing or launching tools.

The prior elastic dot product and multi-module/FIFO/divider results remain in
their separate archives. Target is Artix-7 at100MHz with ideal I/O, not a verified
board deployment; see docs/TARGETS.md. No model-strength comparison is claimed.

Keep source-bound planning and exact candidate dedupe. Additional prior-proposal
prompt context is experimental/opt-in after its study did not establish a benefit.
No held tier, controlled weak-model or product-superiority claim is made.

1. Read `AGENTS.md` and `docs/AGENT_HANDOFF.md` for the working contract.
2. Read `docs/SESSION_HANDOFF.md` for current state and exact next actions.
3. Inspect `git status --short`, recent commits, and `python scripts/session.py status`.
4. Claim the coordinator lease. Respect existing worker file ownership.
5. Read `docs/DECISIONS.md`, `docs/TASKS.md`, `docs/DESIGN.md` and
   `docs/RESEARCH.md` before substantial harness changes.
6. Implement, test, review, and retain evidence. Follow `docs/PUBLICATION.md`
   before declaring archives published. Update shared memory and push
   tested progress. Before switching providers, run the handoff command.

The coordination database in `.autortl/` is local, transactional working state.
`coordination/status.json` is its readable export. Both are machine state, not
Git history. The checked-in handoff, task board, decisions, and test evidence
survive a fresh clone. On another computer, start a new coordinator lease and
reconstruct task ownership from the checked-in handoff.

Checkpointing does not stop the active coordinator or release its lease. Keep
working while usage is available; switch only when necessary. Read the handoff
and test results before starting unattended design campaigns.
