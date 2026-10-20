# Agent harness research and adoption decisions

Reviewed 2026-10-20. Primary sources inform experiments; their reported results
are not AutoRTL results. Decisions below are our engineering assessment, not
claims that the papers validate this implementation. Revisit this record when
an observed failure, repeated cost, or new capability changes a decision.

## Standing rule

Research before designing a substantial new mechanism. State the observed
problem, compare the simplest existing solution, and specify a falsifiable
experiment before implementation. Prefer fewer model calls, deterministic
checks and clearer evidence. A novel architecture is not sufficient justification
for a dependency, extra role, persistent memory system or autonomous action.
Research does not automatically authorize changing the frozen contract or tests.

## Findings and fit

| Primary source | Relevant mechanism | AutoRTL decision and adoption trigger |
|---|---|---|
| [Anthropic: Building effective agents (2024)](https://www.anthropic.com/research/building-effective-agents) | Distinguishes prescribed workflows from model-directed agents; describes evaluator/optimizer and orchestrator/worker patterns, starting simply. | **Keep existing bounded roles.** Our tool sequence and promotion policy stay deterministic. Add a role only when a measured failure needs distinct context or expertise and a same-budget comparison beats a simpler loop. More agents alone is not a reliability result. |
| [Anthropic: Effective harnesses for long-running agents (2025)](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents) | Initial setup, incremental work, progress records, Git history and end-to-end checks carry work between sessions. | **Keep file/Git continuity and evidence-based completion.** START_HERE, task ownership and progress already serve this purpose. Add a structured retrieval index only if coordinators repeatedly fail to recover relevant facts from these files; measure retrieval success and context cost first. A vector database is not currently justified. |
| [SWE-agent: Agent Computer Interface, authors' implementation](https://github.com/SWE-agent/SWE-agent/blob/main/docs/background/aci.md) | Purpose-built feedback, bounded search/viewing and syntax guards improve how agents interact with tools. | **Improve feedback when diagnosis fails.** Existing static checks and bounded report context fit this pattern. Next candidate is a compact first-mismatch record with cycle, expected/actual ports and source/report identities. Implement only after a repair case demonstrates omitted actionable data; compare repair success, calls and tokens against current logs. |
| [AutoChip follow-up (2025), arXiv:2411.11856v3](https://arxiv.org/abs/2411.11856v3) | Iterative compiler/simulator feedback; its study reports that consistent improvement over zero-shot was model-dependent. | **Keep bounded tool feedback; test weak-model benefit.** Do not assume another retry helps every model. Freeze task/model/budget, retain unsuccessful attempts, and compare generate-only against repair feedback. No provider escalation or mixture is added without available models and measured benefit. |
| [MAGE (2024), arXiv:2412.07822v1](https://arxiv.org/html/2412.07822v1) | Separate RTL/test/debug tasks, candidate sampling, and textual state-checkpoint feedback for debugging. | **Test precise state feedback before adding agents.** A short port/handshake trace may help FIFO or streaming repairs. Compare against the existing diagnostic format using known failing designs. Keep frozen acceptance tests independent; do not adopt a judge that edits acceptance tests to rescue a candidate. Candidate diversity needs a fixed-cost N=1 versus N=2 study before expansion. |
| [Google DeepMind: AlphaEvolve (2025)](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) | Generated programs are scored by automated evaluators; an evolutionary program database feeds future proposals. | **Keep objective measurement and the verified incumbent; defer population search.** Existing best-of-N, deduplication and history should be measured first. A population/archive policy becomes worthwhile only if repeated stagnation shows lost useful diversity and gains per model/tool minute improve in a controlled comparison. No new framework is needed for that experiment. |
| [VerilogEval (2023)](https://arxiv.org/abs/2309.07544) and [authors' benchmark repository](https://github.com/NVlabs/verilog-eval) | Functional evaluation against reference behavior across a fixed task set. | **Strengthen independent tests before scaling designs.** Qualify counter8/encoder8 trusted testbenches with behavior-specific mutants, then exercise golden/TB generation separately from trusted integration checks. Simulation success is bounded by coverage; neither this benchmark nor our two tier0 tasks establish formal equivalence or general PPA improvement. |
| [Anthropic: Demystifying evals for AI agents (2026)](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | Separates trials, trajectories, final environment outcomes and graders; supports multiple complementary graders. | **Keep traces plus machine predicates.** Process exits, immutable inputs, simulation verdicts and routed metrics are mandatory; model review supplies additional semantic scrutiny. Missing evidence blocks the run. Evaluate reliability across repeated trials, including infrastructure failures, and separate completion from accepted improvement. |
| [LangGraph: Persistence, official documentation](https://docs.langchain.com/oss/python/langgraph/persistence) | Separates execution checkpoints from application knowledge stored across runs. | **Keep that separation without migrating frameworks.** Runtime journals and development memory solve different problems in AutoRTL. SQLite/file checkpoints already exist. Consider a framework only if a concrete execution requirement exceeds these mechanisms and migration tests preserve replay, evidence and budgets. Checkpointing alone does not make external tool execution and budget charging atomic. |

## Immediate priorities derived from our evidence

1. **Finish exit/input proof validation.** Campaign04 measured a lower-area
   counter but omitted actual exit evidence from review. The current repair
   records real process outcomes, validates raw logs, blocks unknown evidence
   mechanically, and binds reusable simulation to its original inputs. This
   work was motivated by AutoRTL failures; research supports the approach but
   did not establish its correctness. Regression and fresh Vivado runs must.
2. **Measure the generated verification path.** An independent supplied TB
   currently bypasses golden/TB generation for single-module builds. Exercise
   both paths deliberately. Detect wrap, reset, disabled-cycle and priority
   faults before advancing to complex designs.
3. **Ablate existing features.** Under matching budgets, compare the smallest
   generate/verify/repair loop with planning, optional skills, candidate diversity
   and Doctor separately. Record completion, accepted gains, calls/tokens,
   tool/wall time, duplicates and infrastructure blocks. Remove or simplify
   features that repeatedly fail to earn their cost.

## Experiment gate for any proposed feature

Record these in HARNESS_REVIEW or a focused decision entry before implementing:

- Reproduced failure or quantified bottleneck and the affected designs.
- Primary source, proposed mechanism and why the existing code is insufficient.
- Smallest implementation plus simpler alternative; extra roles/dependencies
  and operational costs introduced.
- Frozen tasks, source/TB hashes, device/constraints, runtime and actual model
  identity if observable, budgets and baseline. Unknown model identity prevents
  a controlled model-strength claim.
- Success threshold chosen before running, negative cases, repetitions and
  removal/rollback criterion. A positive unit test alone does not prove a
  benefit to the agent loop.
- Actual outcome, unsuccessful attempts and decision: keep, revise or remove.

Do not copy performance percentages across different datasets, models, tools or
budgets. No external code or dependency was imported during this review. Read
licenses and inspect implementation details before any future code reuse.
