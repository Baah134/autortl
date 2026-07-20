# AutoRTL v4 — Design Document (single source of truth)

When implementation questions arise, the answer is what this document says.

## Thesis
The harness carries the intelligence; the models are replaceable function
calls. Every LLM call is shrunk until a weak model can't fail it; everything
else is deterministic tooling. If the system only performs well with the best
model, the design has failed its own requirement.

## The seven pillars
1. **Task decomposition into module contracts.** The planner's only creative
   output is `design_spec.json` (typed schema in `autortl/spec.py`). Each
   module is an independent generate-verify subtask. Top-level wiring is
   generated mechanically (`linter.top_verilog`) — zero LLM.
2. **Verification ladder.** static checks (ms) → xvlog (s) → unit sim →
   integration sim → synthesis. A candidate that dies at rung 1 costs
   milliseconds, not minutes.
3. **Golden models + generated testbenches.** Python oracle per module,
   qualified against the spec's IO examples first. Testbenches are generated
   code (tbgen.py) in two compare modes: fixed_latency (shift-register
   compare) and scoreboard (queue-based, for valid/ready). Pulse mode is
   deliberately stubbed.
4. **Best-of-N (N=4)** with objective-weighted mutation prompts (bestofn.py),
   hash dedupe, deterministic selection: (rungs, objective metric, brevity).
5. **Error taxonomy** keyed on official Vivado message IDs
   (data/taxonomy.yaml). Unknown IDs: query Vivado's own help, log for
   curation. Severity promotion only — never demote.
6. **Skills** (.claude/skills/, Anthropic SKILL.md format) replace RAG.
   Conventions are law (always in system prompt); skills are optional
   expertise, matched protocol-first (skill_loader.py). Claude Code loads
   natively; harness injects for other backends.
7. **Resumable FSM orchestrator** (fsm.py) with budgets, caches, watchdog.
   Crash anywhere, resume from state.json.

## The six potholes and their fixes (all implemented)
1. Bad blueprint → contract linter + stub elaboration before any generation.
2. Behavioral-vs-cycle-accurate → latency field + two compare modes;
   spec-is-law via `// @latency N` header (mismatch = graded failure).
3. Anchored horde → forced architectural mutation portfolios + dedupe.
4. Replan amnesia → contract-hash artifact cache; unchanged modules imported;
   max 2 replans with budget-forced degradation.
5. Pattern library square peg → protocol-first matching from spec metadata.
6. Timing gap → Timing Doctor: tool knobs (retiming/phys_opt) first, RTL
   surgery second (slack -0.5/-3.0 ns thresholds), replan last.

## The six defences (all implemented)
7. Testbench qualification by bug injection (tbqual.py) — the oracle must
   FAIL a sabotaged design before it grades anything.
8. Reset/X discipline — reset per spec + 2-cycle settle before comparing.
9. Infra-vs-design triage (triage.py) — infra failures never mutate the
   design or enter history.
10. Metrics integrity gates (metrics_gate.py) — the lut_total:0 class of bug
    is fatal, never a silent score.
11. TCL injection boundary — LLM output only in .v files; paths sanitised.
12. Router stats — recording-only (llm/router_stats.jsonl) until ~10 runs.

## Provider architecture
`llm/routing.yaml` is the policy: per-role chains over three backends
(claude_code headless, nvidia NIM, openrouter free Nemotrons). Planner+doctor
get best-available (opus→sonnet); generator+evaluator pinned sonnet.
Generator/evaluator run --max-turns 1 (deliberately de-agented); the doctor
gets max_turns 3. OpenRouter 429s are infra.

## Modes
- `optimize`: existing design+tb in, contract negotiated about metrics.
- `build`: intent → spec → lint → stubs → per-module build → mechanical
  integration → flows into optimize as its baseline.
- `resume`, `bench` complete the CLI.

## Curriculum governance
Tier held = 3 consecutive runs ≥80%. Regressions on held tiers block harness
changes. Stage gates: S1-2→tier0-1, S3-4→tier2, S5→tier3, S6-7→tier4-5.
Tier 4 = RTLLM v2 / VerilogEval; CRADLE's 48% LUT / 40% FF is the number to
beat.

## Conventions (enforced by autortl-conventions skill + code)
Spec is law (latency, interfaces). Promote never demote. One driver per
signal. Defaults first in combinational blocks. Clock is `clk`. All TCL from
harness templates only.

## Deferred by decision (not forgotten)
Pulse compare mode; LLM watchdog-diagnosis layer; router reordering (after
10 runs); Tier-3 skill regression evals; formal verification rung.
