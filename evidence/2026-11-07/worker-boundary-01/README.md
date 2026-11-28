# Restricted Codex text-generation workers

The original backend inherited enabled MCP integrations despite its read-only
cwd and no-tools request. This batch restricts child configuration, verifies no
MCP server remains enabled, disables supported capabilities/web and rejects
unexpected tool trajectories. Authentication, managed/security environment,
read-only sandbox and execpolicy rules remain in force. No weaker fallback.

Software: 2074 passed in 646.94s (0:10:46); 323 passed, 1 skipped in 110.73s (0:01:50). All 340 frozen inputs unchanged. The new JSONL
fixture is explicitly frozen even though the gate suffix set excludes JSONL.
Independent review found and closed a deadline edge before process launch.
Original failures, corrected fixtures, staged patches and source snapshots are
retained. Provider tests preserve their quota/auth/redaction/cleanup assertions.

One real requested gpt-6-luna text control returned the exact expected token,
with policy metadata and zero observed tool items. Actual model identity was
unobserved; price is unknown. This was a compatibility test, not a design or
benchmark verdict. Installed CLI hash/version and configuration checks are
recorded. No FPGA, JTAG, serial, hardware server or programming action occurred.

Ignoring user configuration changes default model/provider semantics; explicit
model names remain requested names but do not restore custom CLI providers.
Use AutoRTL's explicit endpoint backend for custom endpoints. This versioned
configuration restriction is not a complete tool-catalog or OS isolation proof.
Post-execution event rejection cannot undo effects. The public benchmark still
requires independently qualified grading isolation.
