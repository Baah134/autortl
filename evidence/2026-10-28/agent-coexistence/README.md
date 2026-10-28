# Sequential agent accommodation — October 28

The user wants Codex and Claude Code to take turns. Existing coordinator leases,
scoped tasks and explicit handoff already support that policy; no concurrent-worker
implementation or new orchestration framework was added. Startup instructions now
require live ownership/process checks and preserve dirty work and spent budgets.

source-identity.json records unchanged executable/design inputs across this
documentation update. Coordination tests exercise actual Codex-to-Claude handoff,
expired-lease reclaim, simultaneous coordinator claims, scope conflicts, rollback,
completed-task evidence and token-free exported status. The test receipt/log record
the actual invocation and result; they do not imply a new FPGA gate or full suite.

Prior FIR02 evidence and the unfinished campaign13 were not modified or regraded.
Main runtime integration still requires its pending complete FPGA regression gate.
