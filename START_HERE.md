# AutoRTL shared project memory

Canonical checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
Development: `codex/contract-context`. Main remains `ca61dbc` pending final release.
Current checkpoint: **November 7, reliability corrections and release preparation**.

Read `AGENTS.md`, `docs/AGENT_HANDOFF.md` and the latest section of
`docs/SESSION_HANDOFF.md`, then verify live SQLite ownership, Git and processes.
One coordinator leads; its scoped subagents may work in parallel. Never replay
old staged patches or overwrite another coordinator's active work.

Development commit `b59d077` published 22 completed signoff4 archives: all
49,435 committed blobs were verified. The original sign-off has stopped.
Tier6-02 passed 2,022 harness tests, then all three entries hit CODEX_QUOTA.
Its final launch receipt is missing and it has **no design verdict**. The
96-file archive and 334 original source inputs were verified before new edits.
Latest valid recorded holds remain tiers 0–5 on their earlier runtime identity;
tier 3 is 4/5 with a UART/FIFO failure, and tier 6 is 2/3, not held.

Current work: independently reviewed planner sampling guidance and exact source
identity pruning are integrated. Software checks: 2028 harness tests and
323 tooling tests passed; one Windows symlink-privilege test skipped. Three
real XSIM sampling controls passed their declared positive/negative outcomes.
The portable replay also passed. Read evidence/2026-11-07/reliability-01.
New model exploration waits for a verified worker tool restriction; the CLI
currently inherits local MCP configuration. Source changes require a new run.
The user connected the FPGA; this stage does not access or program the board.

`docs/ACTION_PLAN.md` defines the finite release: finish demonstrated reliability
work, freeze a candidate, run a predeclared public-task comparison, and package
the hardware/verification evidence. Benchmark superiority is not established.
Do not re-hold finished tiers during development; the final release pass gates
main integration. Use only fresh attempt directories and original budgets.

Shared memory belongs here and in the docs, not in the public README. Update
the checkpoint after substantial progress and publish tested milestones.
Checkpointing keeps coordinator ownership; release it only when actually leaving.
