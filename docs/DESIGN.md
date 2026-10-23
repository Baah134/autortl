# AutoRTL v4 — Design Document (single source of truth)

This document describes the intended architecture. Runtime code and retained
verification evidence establish implemented behavior; docs/HARNESS_REVIEW.md
records feature coverage, limits and simplification decisions.

## Thesis
The harness carries the intelligence; the models are replaceable function
calls. The goal is small, explicit model tasks backed by deterministic
verification and actionable repair feedback. Weak-model reliability is an
experimental target, not an established result. If the system only performs well with the best
model, the design has failed its own requirement.

Optimization contracts are rendered mechanically from frozen harness evidence.
Model roles do not negotiate or amend their verification requirements.

Structural interface checks preserve signedness, packed shape and symbolic
public-parameter declarations; see [interface contracts](INTERFACES.md) for the
supported schema and limits.

## The seven pillars
1. **Task decomposition into module contracts.** The planner's only creative
   output is `design_spec.json` (typed schema in `autortl/spec.py`). Each
   module is an independent generate-verify subtask. Top-level wiring is
   generated mechanically (`linter.top_verilog`) — zero LLM. A validated complete
   transparent single-child wrapper inherits that child's known latency contract;
   arbitrary module graphs receive no inferred aggregate numeric latency.
2. **Verification ladder.** static checks (ms) → xvlog (s) → unit sim →
   integration sim → synthesis. A candidate that dies at rung 1 costs
   milliseconds, not minutes.
3. **Golden models + generated testbenches.** Python oracle per module,
   qualified against the spec's IO examples first. Testbenches are generated
   code (tbgen.py) in two compare modes: fixed_latency (shift-register
   compare) and scoreboard (queue-based, for valid/ready). Pulse mode is
   deliberately stubbed.
   Scoreboard stimulus includes unique complete payload vectors from declared
   examples that explicitly assert input-valid and deassert the configured
   reset. Scheduling remains driver-owned; oracle outputs remain authoritative.
   Three existing corners and the seeded random tail are preserved. This is
   payload coverage, not replay of example timing/state traces. Fixed-latency
   example sequences are unchanged; total stimulus plus reset remains bounded.
4. **Best-of-N (N=4)** with objective-weighted mutation prompts (bestofn.py),
   hash dedupe, deterministic selection: (rungs, timing feasibility, objective
   metric, brevity). A verified timing recovery can use more resources; it is
   recorded separately from objective savings.
5. **Error taxonomy** keyed on official Vivado message IDs
   (data/taxonomy.yaml). Unknown IDs: query Vivado's own help, log for
   curation. Severity promotion only — never demote.
6. **Skills** (.claude/skills/, Anthropic SKILL.md format) replace RAG.
   Conventions are law (always in system prompt); skills are optional
   expertise, matched protocol-first (skill_loader.py). Claude Code loads
   natively; harness injects for other backends.
7. **Resumable FSM orchestrator** (fsm.py) with budgets, caches, watchdog.
   Crash anywhere, resume from state.json.

## The six potholes and intended fixes (see handoff for verified status)
1. Bad blueprint → contract linter + stub elaboration before any generation.
2. Behavioral-vs-cycle-accurate → latency field + two compare modes;
   spec-is-law via `// @latency N` header when the current top declaration
   is known (mismatch = graded failure). Unknown annotation metadata is not zero
   and cannot justify a missing-header rejection. Typed child contracts still
   require numeric latency; scoreboard latency is minimum accepted-transfer age,
   with later delivery possible under backpressure.
3. Anchored horde → forced architectural mutation portfolios + dedupe.
4. Replan amnesia → contract-hash artifact cache; unchanged modules imported;
   max 2 replans with budget-forced degradation.
5. Pattern library square peg → protocol-first matching from spec metadata.
6. Timing gap → Timing Doctor: tool knobs (retiming/phys_opt) first, RTL
   surgery second (slack -0.5/-3.0 ns thresholds), replan last.

## The six defences (see handoff for verified status)
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
`llm/routing.yaml` routes planner, generator, evaluator and timing doctor to
`codex.default`. Each call starts a bounded Codex CLI worker with the existing
login and configured default model. Legacy provider files are historical;
the active client cannot invoke them. No additional API key is required.

Workers receive prompts over stdin in a temporary working directory with a
read-only sandbox and ephemeral session. The harness requires a completed
JSONL turn and nonempty final response. Usage is recorded when reported;
unknown model/cost stays null. Timeouts and cancellation terminate the owned
worker, including a Windows process-tree termination attempt. The adapter
enforces wall time, not the historical max_turns parameter. Read-only is not
a guarantee that the worker has no tools.

These are independent role invocations. The development-session coordinator
and its helper agents supervise integration; persistent runtime dialogue and
fully reliable FSM resume remain separate development work.

## Modes
- `optimize`: existing design+tb in, fixed contract rendered from frozen evidence.
- `build`: intent → spec → lint → stubs → per-module build → mechanical
  integration → flows into optimize as its baseline.
- `resume`, `bench` complete the CLI.

## Curriculum governance
Tier held = 3 consecutive runs ≥80%. Regressions on held tiers block harness
changes. Stage gates: S1-2→tier0-1, S3-4→tier2, S5→tier3, S6-7→tier4-5.
Tier 4 targets RTLLM v2 / VerilogEval. External optimization percentages require
matched tasks, technology, tools, contracts and budgets before comparison; see
[research decisions](RESEARCH.md) for CRADLE and other related systems.

## Conventions (enforced by autortl-conventions skill + code)
Spec is law (latency, interfaces). Promote never demote. One driver per
signal. Defaults first in combinational blocks. Clock is `clk`. All TCL from
harness templates only.

## Deferred by decision (not forgotten)
Pulse compare mode; LLM watchdog-diagnosis layer; router reordering (after
10 runs); Tier-3 skill regression evals; formal verification rung.

## Exit evidence and latency authority

Each tool invocation writes tool_exit_records.log with actual process exits,
distinct driver outcomes, process identity, duration and output-log hash.
Timeout124 and launch126/127 are driver codes, never successful process exits.
Context validates the full receipt history and exposes bounded records plus
latest outcomes. Cache and DONE retain evidence hashes; source-identical physical
Doctor trials explicitly cite prior simulation evidence rather than claim reruns.

Unannotated optimization inputs have unknown declared numeric latency. They do
not acquire a zero-cycle contract; every observable source cycle remains fixed.
Typed builds require known numeric latency for generated reference comparisons.
An annotation alone is never independent proof of behavior.

Curriculum cohorts bind tasks, configuration, frozen implementation/Python/tool
identity and governance code. Missing or mixed runtime provenance cannot qualify
a tier. CLI model identity remains unobserved; a tier result does not establish
a frozen-model experiment or weaker-model robustness.
