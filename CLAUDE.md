# AutoRTL — notes for Claude Code

The rules for every agent are in [AGENTS.md](AGENTS.md); follow them exactly.
The plan is [docs/ROADMAP.md](docs/ROADMAP.md), the current state is
[docs/SESSION_HANDOFF.md](docs/SESSION_HANDOFF.md), and the architecture is
[docs/DESIGN.md](docs/DESIGN.md), the single source of truth; read it before
changing the harness.

## What this repository is

A harness that writes and optimizes Verilog with bounded model roles and
verifies everything through AMD Vivado: the model proposes, deterministic
checks decide. `benchmark/` compares it with a single model call on public
tasks.

## Layout

`autortl/` harness (orchestrator `fsm.py`, roles, prompts, testbench
generation and qualification, Vivado driver, triage, metrics gate) ·
`llm/` model client, backends, `routing.yaml` · `.claude/skills/` conventions
and expertise injected into prompts · `data/taxonomy.yaml` message IDs and
failure modes · `curriculum/` tiered designs · `benchmark/` VerilogEval
adapter, arms, campaign, report · `hardware/basys3/` board shells and checkers
· `evidence/` hashed result archives · `tests/` regression suite · `run.py`
CLI (`optimize | build | resume | bench | doctor`).

## Working here

- Take turns with other coordinators: check `python scripts/session.py status`
  before editing, claim the lease and file scopes, hand off when leaving.
- Before committing a harness change: `python -m pytest tests/ -q` (full
  suite) and the tooling suite. Curriculum tiers are re-held once at the
  release gate, not after every change.
- Windows host. Vivado 2025.2 at `C:\AMDDesignTools\2025.2`; pass absolute
  `.bat` tool paths (`python run.py doctor` finds them). TCL paths are
  forward-slash absolute. Batch `xvlog`/`xelab`/`xsim`, no project mode.
- Models: roles route through `llm/routing.yaml` (Codex CLI by default; set
  `AUTORTL_CODEX_BIN` if it is not on PATH) or `--model` for any configured
  backend. No silent fallback to another provider.
- Shell heredocs mangle backslashes; write regexes and escaped strings with a
  file editor, not through `python - <<EOF`.
