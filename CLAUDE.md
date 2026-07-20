# AutoRTL v4 — instructions for Claude Code sessions

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
- CURRENT STATE: all seven stages implemented; tier0-1 curriculum seeded;
  84 harness tests passing. Next: first live run on tier0, then grow tiers.
- Before merging any harness change: `python -m pytest tests/ -q` and
  `python run.py bench --tier 0` (plus the highest held tier).
- Windows: Vivado lives at C:\AMDDesignTools\2025.2. TCL paths are
  forward-slash absolute. Batch xvlog/xelab/xsim, no project mode.

## Layout
autortl/ (harness) · llm/ (backends+routing.yaml) · .claude/skills/ (law +
expertise) · data/taxonomy.yaml (message IDs) · curriculum/ (tiered tests) ·
tests/ (pytest) · run.py (CLI: optimize|build|resume|bench)

## Env vars
NVIDIA_API_KEY (NIM fallback), OPENROUTER_API_KEY (free Nemotron fallback).
Claude Code itself is the primary backend via `claude -p`.
