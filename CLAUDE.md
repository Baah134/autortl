# AutoRTL v4 — project contract (historical filename)

For Claude and its subagents: start at `START_HERE.md`, then read `AGENTS.md`
and `docs/AGENT_HANDOFF.md`. These are the same shared memory and ownership
rules used by Codex and Gemini. The current runtime client uses Codex, while
development coordination may use any user-authorized agent.

## What this repo is
A harness-first agentic system that writes and optimises Verilog through
Vivado. Read docs/DESIGN.md before changing anything — it is the single
source of truth. This file is the standing session contract.

## Hard rules (from DESIGN.md, non-negotiable)
- Spec is law: never let generated code change a contract latency or
  interface; mismatches are failures, not negotiations.
- LLM output lands only in .v / .py files. Never interpolate model strings
  into TCL, shell commands, or paths.
- Vivado message severities are promoted only, never demoted or suppressed.
- Infra failures (locks, licenses, 429s, timeouts) never mutate the design,
  never enter history, never count as fix attempts.
- Every parser gets a pytest with a fixture file. Every new failure mode
  becomes a taxonomy entry or curriculum entry BEFORE the hotfix lands.

## Working protocol
- One stage per session where possible. Current stage: see docs/DESIGN.md
  build order; update the line below when a stage gate passes.
- CURRENT STATE: see docs/SESSION_HANDOFF.md and docs/PROGRESS.md for verified
  results and remaining gaps. Runtime model calls use Codex only.
- Before merging any harness change: `python -m pytest tests/ -q` and
  `python run.py bench --tier 0` (plus the highest held tier).
- Windows: Vivado lives at C:\AMDDesignTools\2025.2. TCL paths are
  forward-slash absolute. Batch xvlog/xelab/xsim, no project mode.

## Layout
autortl/ (harness) · llm/ (backends+routing.yaml) · .claude/skills/ (law +
expertise) · data/taxonomy.yaml (message IDs) · curriculum/ (tiered tests) ·
tests/ (pytest) · run.py (CLI: optimize|build|resume|bench)

## Env vars
AUTORTL_CODEX_BIN optionally selects the Codex CLI executable. Otherwise it
must be on PATH. Use existing Codex login; no external-model fallback.
