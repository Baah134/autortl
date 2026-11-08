# AutoRTL action plan — November 6, 2026

Goal: ship a reproducible FPGA/EDA portfolio release with working hardware,
independent verification and a defensible comparison against simpler workflows.
The harness is the contribution; its demonstrations and evidence establish scope.

## Verified starting point

- Development base e61665c5; checked remote main ca61dbc. Several October29
  review fixes are now integrated; do not replay the obsolete staged patches.
- Twelve archived designs have Basys3 hardware checks. Hardware shell clock is
  distinct from a core's out-of-context timing target; report each separately.
- Latest completed harness regression receipt: 2,022 passed. README's aggregate
  count must be reconciled with separately named harness and tooling suites.
- Signoff4 full records hold tiers0–5 on the recorded runtime. Tier3 qualifies
  at4/5; uart_fifo_build repeatedly failed. A held tier is not universal success.
- Tier6 first campaign passed CORDIC/RV32I but failed AES oracle construction.
  The generated aes_round oracle indexed255 in a255-element exponent table.
- Original signoff4-t6-02 subsequently stopped: 2022 software tests passed,
  then model quota blocked all three entries. No design verdict; final launch
  receipt missing. Its 96-file archive and 334 original frozen inputs match.
  Preserve it as an incomplete infrastructure-blocked attempt.

## Execution order and completion criteria

| Order | Work | Completion evidence |
|---|---|---|
| 1 | Preserve existing sign-off, validate completed archives, repair stale current-state memory | Every completed manifest hashes correctly;334 frozen files unchanged; live IDs and next action recorded; completed evidence published to development |
| 2 | Finish the current tier6 attempt and diagnose recurring AES/UART failures | Actual exits, role replies and first mismatches retained; distinguish model failure, harness bug and infrastructure interruption; no fabricated verdict or budget reset |
| 3 | Close demonstrated reliability gaps in one reviewed batch if needed | Reproduced failure before correction, meaningful regression afterwards, full software checks; no changes while a frozen job runs |
| 4 | Freeze a release candidate and establish the benchmark protocol | Dataset commit/license/task IDs fixed; separate pilot set; model/backend identity, prompts, graders and budgets recorded; comparison arms cannot edit the external grader |
| 5 | Run the public-task comparison |30–50 predetermined tasks,3 independent trials,3 arms=270–450 runs; retain all failures, cost, tokens, time and intervention; report uncertainty and false acceptance |
| 6 | Package and release | Concise README, architecture diagram, runnable demo, CI, case studies, source/bitstream traceability, hardware demonstration recording and interview walkthrough; audit and final sign-off gate main integration |

Do not repeatedly re-hold finished tiers during development. Preserve the user's
November1 rule: intermediate changes use regression and current/harder-tier
exploration. Re-hold the final release identity at the end. The current signoff4
is already that final-pass attempt; do not start a duplicate pass beside it.

## Benchmark protocol

First validate adapters with a small pilot excluded from final results. Choose
one public dataset revision and declare inclusion criteria before generating
results. Keep interface conversion explicit and deterministic; ambiguous tasks
are classified before trials, not removed after failures.

Compare (A) one model call, (B) the bounded loop with selected internal
verification safeguards ablated, and (C) the full harness. The external final
grader, execution isolation, contract, immutable inputs and budget accounting
apply to all three. A result accepted by an arm but rejected by that grader is
a false acceptance. An ablation is an experiment setting, not the shipped default.

Use the same model/configuration and declare per-arm budgets. Report verified
success against actual cost; extra feedback calls are not free. Three repeats
per task are clustered by task when summarizing uncertainty. Public tasks do
not establish freedom from training contamination. Claims of superiority to a
general coding agent need a tools-enabled agent baseline as a separate comparison.

Functional benchmark results and FPGA area/timing results are distinct. Measure
routed PPA only for correct designs under matching target/constraints, retaining
DSP/BRAM/FF and estimated-power tradeoffs. A negative result is publishable;
never tune the held-out set to manufacture a headline.

## Reviewer package and ownership

Lead with three verified outcomes: physical hardware, qualified verification,
and measured comparison (once completed). Link full logs and implementation
details from the short front page. Explain handwritten shells/parameter overrides
and agent-generated cores accurately. Describe AI-assisted development and the
owner's architectural and verification decisions explicitly.

Case studies: FIR timing/area recovery; generated-verifier18/27 to22/27 with
five remaining misses; one complete hardware integration. The walkthrough should
explain tbgen, tbqual, the FSM, reset/backpressure, signed widths and rejected
optimizations from actual code and reports.

## Agent responsibilities and operational limits

One coordinator integrates and owns the existing tool queue. Subagents may
independently audit sign-off/evidence, review hardware claims, or prepare an
isolated benchmark adapter. Each has an explicit scope and reports raw results.
They cannot edit frozen inputs or launch a second model/vendor campaign.

Already dispatched: independent sign-off reconciliation and hardware/release
claim review. After the active attempt finishes, assign bounded failure
diagnosis and implementation only where the evidence requires it.

The release is complete when another person can clone it, run the documented
software checks/example, reproduce the retained hardware image/test protocol,
inspect benchmark results and distinguish measured results from assumptions.
Git activity, more agents and a larger tier number are not completion criteria.

## Parallel diagnosis results — November6

Evidence: evidence/2026-11-06/parallel-diagnoses-01. AES's three oracles were
correctly rejected; a bounded previous-source/error repair study is conditional
on recurrence. UART failures show a pre-edge latency0 versus post-edge stateful
model mismatch; an independent Python probe explains the recorded assertions.
A planner sampling-clarity correction is being prepared in isolation, with
controls, while the active implementation remains frozen. The benchmark protocol
proposes40tasks plus6disjoint pilots and360scored runs; it is not yet registered
or executed and requires a real independent grading boundary and adapter.

## November 7 execution update

Steps 1–2: completed archives published in b59d077 (22 archives, 49,435
committed blobs verified). Original sign-off stopped with quota/no verdict;
the controller outcome and incomplete receipt are preserved. Step 3 is in
validation: explicit sampling guidance and worktree pruning, independent
reviews, real simulator controls, full software regression. No retries or
budget expansion, hidden test changes, new roles or board actions.

No benchmark trials or superiority result yet. Dataset pin/adapter review
does not select the scored task roster or freeze a final release identity.

Reliability software acceptance completed:2028 harness+323tooling passes;
one explicit Windows symlink-privilege skip,337 frozen inputs unchanged, and
three real sampling controls plus portable replay. Reader case studies now
explain FIR4's measured tradeoff and the verifier's18/27→22/27 correction.
Before another model exploration, restrict inherited worker tool capabilities
and validate the effective boundary; requesting no tools is insufficient.
No board command is authorized by this work stage.

## November8 execution boundary

The finite AES study ended with AES04: round oracle qualified, all four round RTL candidates failed. No AES05/task-specific tuning follows. The independently reviewed benchmark artifact foundation is validated (see BENCHMARK_ARTIFACTS and its evidence). Candidate export/selection, actual mutation-only policy, grader isolation and failed-call accounting remain necessary before disjoint pilots and final registration. No benchmark result or final main integration is claimed.
