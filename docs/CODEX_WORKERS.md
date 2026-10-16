# Codex workers

All active runtime roles use Codex CLI through the existing local login.
No Claude, Gemini, NVIDIA, or OpenRouter account is required or used.
The default model is inherited from Codex configuration. Model usage and
timeouts still apply; this does not create unlimited background execution.

Check `codex login status`. Set `AUTORTL_CODEX_BIN` if codex is not on PATH.
On Windows use a writable TEMP/TMP directory if sandbox temporary files are
restricted. The worker uses a fresh directory, stdin prompts, read-only mode,
ephemeral sessions, JSONL events and a final response file. Raw model output
is an unverified proposal until the harness checks it.

## First supervised generation trial

From the repository with Python dependencies installed:

```powershell
python scripts/check_codex_counter.py --bin-dir C:/AMDDesignTools/2025.2/Vivado/bin --output runs/codex-counter-001
```

The output directory must be new. This permits one model call, generates an
8-bit counter, checks static structure, runs an independently written 700-cycle
testbench, confirms that the same testbench rejects stuck-zero and asynchronous-reset mutants, and
runs synthesis/placement/routing with required timing closure. It records prompt, response, source/test
hashes, stage events, model metadata and reports. It is a supervised generation
check, not the build FSM or an optimization campaign. Vivado launch may require
approved execution outside the desktop sandbox on Windows.

Use `--source <saved-counter8.v>` to reverify a saved proposal without another
model call. The default implementation timeout is 600 seconds; override with
`--implementation-timeout`. Tool elapsed time is charged separately from model
calls. A timeout is retained as an infrastructure failure, never a design pass.

## Supervision and limits

The main development agent delegates implementation and independent review,
then integrates and tests. Runtime planner/generator/evaluator/doctor are
separate bounded Codex invocations. They do not yet form a persistent dialogue.
Only the deterministic harness can establish correctness from tool evidence.

Calls charge the budget before launch, including failed attempts. Unknown
monetary cost is null. The legacy max_turns argument is not enforced by Codex
CLI; wall time is bounded. Read-only mode does not disable all tools. Windows
timeout/cancellation cleanup targets only the owned worker PID and descendants;
OS failures can prevent complete tree cleanup.

Before unattended optimization: repair resume, build generation and testbench
generation; finish cache/Timing Doctor evidence integrity and infrastructure
round accounting. Consult SESSION_HANDOFF.md for the latest tested state.

Integration reference: [official Codex non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode).
