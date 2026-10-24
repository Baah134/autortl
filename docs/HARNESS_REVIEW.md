# Harness effectiveness review

Updated 2026-10-21. The objective is to make a bounded, reliable harness that
extracts useful work from weaker models. Design results are probes of that
system. No weaker-model performance has been demonstrated yet.

## Historical campaign05 findings

- At that checkpoint: **655 regression tests passed**. Fresh campaign05 completed
  **2/2**, with accepted counter55to53LUT (3.6%), FF37, WNS0.456ns/
  WHS0.282ns. Mux8LUT baseline retained because its candidate had no gain.
  Three model calls per design; actual DONE replay preserved the counter
  winner/budget/summary without added tool/model calls. One bounded accepted
  gain, no held tier and no weaker-model claim.
- At the preceding checkpoint,554 regression tests passed. The counter32 reference checks every output and
  detects all four selected mutants in real Vivado simulation. Earlier nine
  generated-testbench cases cover positive and negative timing/streaming cases.
- Earlier cohort tier0_fkxbmmwe originally finished 0/2 after worker exits, not failed
  RTL. Counter generation and the complete physical ladder succeeded before its
  evaluator failed; mux completed its baseline before its planner failed.
- Counter baseline: 55 LUTs/37 FFs, setup slack 0.494 ns, hold slack 0.113 ns.
  Candidate: 53 LUTs/37 FFs, setup slack 0.456 ns, hold slack 0.282 ns. Both use
  the same independent testbench, device and 10 ns/ideal-zero-I/O assumptions.
- Real counter recovery retried one evaluator call, preserved all completed
  physical stages and kept tool time at 267.641 seconds. The evaluator rejected
  the candidate because its context omitted the routed timing report identity.
  That report exists. The lower LUT count is measured, but the harness did not
  promote it; do not claim an accepted autonomous improvement.

The rejection is an evidence-delivery defect, not justification for weakening
verification. It also demonstrates why model opinions about available evidence
should not substitute for explicit machine predicates.

## Keep, improve, simplify

| Decision | Feature | Evidence and action |
|---|---|---|
| Keep | Verification ladder and metric integrity | Exercised on real baselines/candidates. Reject missing metrics and failed setup/hold; preserve exact source-to-report linkage. |
| Keep | Independent reference tests and mutation qualification | Actual bug detection catches changed latency, high-bit comparisons, reset and overflow semantics. Expand before increasing complexity. Mutation coverage is not a proof of all behavior. |
| Keep | Atomic journals and immutable context | Controlled interruption/tamper tests and real provider recovery exist. Add real process interruption coverage and preserve accounting. |
| Improve now | Report evidence delivered to roles | Timing/utilization/power identities now reach live review. Campaign04 exposed a further missing actual-process-exit proof; durable receipts and deterministic gates pass fresh live campaign05. |
| Improve now | Worker diagnostics and blocked outcomes | Implemented bounded redacted diagnostics, typed provider failures and resumable model-blocked outcomes. Budget stops retain the verified best pointer. Controlled replay tests validate recovery; live provider recovery was already observed at the prior revision. |
| Simplify | Prose contract negotiation | Campaign02 spent six calls on wording and blocked counter before generation. Replaced optimization negotiation with a deterministic contract from immutable evidence; preserve all verification and final promotion gates. |
| Improve next | Acceptance policy | Define machine-checkable mandatory predicates and make model review advisory for their measurable portions. Preserve genuine semantic checks; add tests for any bug a reviewer finds. Do not simply bypass a rejection to publish a gain. |
| Improve | Legal mutation portfolio and Doctor | Mutation and surgery prompts now preserve latency/reset/parameter semantics. Canonical setup/hold diagnosis maps hold failures to physical hold fixing, then replan. Supervised hold-fix command run passes routing but raises mux area from8to18LUTs; keep it targeted. Full autonomous Doctor repair remains unproven. |
| Validate live | Contextual cache, build, golden process and restart | Regression coverage exists. This cohort does not prove live build, cache reuse, restart or general interruption recovery. Exercise each explicitly. |
| Measure | Best-of-N diversity, skills, watchdog and advisor | Current cohort uses N=1. Their marginal benefit has not been measured; do not present them as established gains. |
| Remove or disable clearly | Dead module-cache branch and unused controls | Removed unreachable module-cache branch and writes; verified journal reuse remains. False parallel_candidates stays compatible; True now errors explicitly because execution is sequential. |
| Keep historical only | Legacy provider adapters and max_turns argument | Active runtime is Codex-only. max_turns is not enforced. Do not advertise these as working runtime capabilities. |

## Next feature coverage experiments

1. Recovery and archival completed. Original cohort 0/2 and recovered per-run
   outcomes remain separate; neither recovered run promoted a candidate.
2. Validate repaired report-provenance and worker-diagnostic boundaries with
   regression tests and a fresh bounded campaign.
3. Run counter8 and encoder8 typed builds to exercise golden execution,
   generated TBs, qualification, integration and final physical measurement.
4. Use a pipeline/streaming case to exercise latency and backpressure; inject
   timing failures to exercise Doctor and verify its output through the ladder.
5. Force a repeated candidate and changed constraints to test live deduplication
   and cache reuse/invalidation. Force stagnation to test restart.

## Measure whether a feature earns its complexity

Freeze tasks, source/TB hashes, device, constraints, model identity and budgets.
Compare a minimal generate/verify/repair loop against planning, selected skills,
N-candidate diversity and Doctor, adding one feature at a time. Record completed
runs, correctness failures, infrastructure blocks, accepted improvements, calls,
reported tokens, tool time, duplicate candidates and recovery behavior.

Use repeated runs and an actually available weaker model before making model
robustness claims. Mutation tests establish verifier sensitivity, not weak-model
success. Keep unsuccessful attempts in the denominator. A layer should remain
only when it improves reliability, verification strength or measured efficiency.

## Timing repair implementation references

Physical hold fixing uses `phys_opt_design -hold_fix` after placement and before
routing, without RTL delay chains or synthesis retiming for hold-only trials.
AMD documents the physical option in [UG835](https://docs.amd.com/r/2024.2-English/ug835-vivado-tcl-commands/phys_opt_design).
Local Vivado 2025.2 execution remains the acceptance evidence for this environment;
command-generation tests alone are not proof that a hold violation was repaired.

## Assembled guidance audit

Campaign02 at61854c0 finished0/2: counter contract wording blocked after six
calls; mux saved a live CODEX_QUOTA model_blocked outcome with baseline retained.
This is separate from campaign01/recovery and remains a failed cohort.

The actual prompt audit found six role calls missing conventions, a nonexistent
planning skill, contradictory latency/reset/inference advice, and an unsafe
referenced FIFO full comparator. Repairs align every injected skill with the
fixed contract, add the short planning checklist, enforce conventions in every
role and count headings/separators in the skill injection budget. Tests inspect
assembled calls, not just template strings. FIFO reference qualification at two
depths checks transaction behavior; it cannot establish metastability reliability
or physical CDC closure. Multi-clock physical implementation is not demonstrated.

Feature value remains an experiment: instruction consistency is required for
correctness, while the marginal benefit of each optional reference still needs
controlled ablation. Do not add agent layers merely to increase agent count.


## Structural checks and persistence audit

Campaign03 reached useful generation without negotiation but exposed a Windows
atomic budget replacement error. Bounded Windows-only retry now has controlled
fault tests and a real sharing-lock test. Persistent storage failure/hard-kill
accounting is still not an external transaction; no exact recovery claim follows.

Default-width comparison was insufficient: six reproduced public-parameter,
signedness and packed-shape bypasses are now rejected. Signed/shape metadata and
symbolic interface dependencies reach mechanical code generation as well as
static gates. Four live signed/parameter control-and-mutant cases qualify the
new paths. These checks preserve declarations, not all parameterized behavior.

Retain the verification ladder and deterministic contracts. Next live coverage
still needs typed build/golden integration, cache/restart and complete Doctor
invocation; optional planning/skill/best-of-N benefits need controlled ablation.

## Campaign04 evidence audit

Frozen2318e42 completed tier0 **2/2 mandatory gates**, the first qualifying
cohort; not a held tier. Both runs used three model calls. Neither promoted a
candidate. Counter measured53vs55LUT but its evaluator lacked actual process
exit codes. A log marker is not an exit record. The next repair retains actual
process/driver outcomes separately and carries their hashes through evaluation,
cache and DONE. Tool-only Doctor trials must identify reused simulation evidence
against unchanged source, without implying simulation reran.

The mux had no objective gain and exposed absent latency metadata being
presented as zero. An unannotated existing design has unknown declared latency;
its observable cycles remain fixed by source and independent tests. Typed
builds still need an explicit numeric latency. This distinction must reach
generation, checks and evaluation.

Curriculum task/config identity alone cannot establish a frozen three-run
streak. Runtime and governance implementation identity must also match; unknown
provenance cannot support qualification. CLI model identity remains unobserved,
so no controlled comparison between model strengths follows from a held tier.

## Research policy (2026-10-20 user direction)

[Research ledger](RESEARCH.md) maps primary literature and engineering reports
to observed AutoRTL needs, simple alternatives, adoption triggers and tests.
Reviewed workflow/evaluator patterns, long-running continuity, SWE-agent's tool
interface, AutoChip/MAGE RTL feedback, AlphaEvolve's measured search, VerilogEval
and execution-versus-knowledge persistence. No new framework, provider, memory
service or agent layer is justified solely by this review. First strengthen
evidence and independent verification, then ablate existing optional features.

## Fresh05 result and next feature decision

The counter now passes the exact evidence requirement that blocked campaign04:
all actual latest tool exits are successful and raw logs match their hashes.
The evaluator passes8/8criteria and the deterministic gates promote iteration1.
Mux review passes behavioral/physical criteria and rejects its unchanged8LUT
objective; baseline retention is the expected outcome. Full tier0 is2/2,
runtime-bound streak1, not held. No gate was removed to obtain the counter gain.

Completed-run replay is now live checked; in-flight hard-kill accounting is
still unproven. Keep improving independent verification before population search,
extra roles or a framework migration. Generated golden/build integration and
behavior-specific trusted-TB mutations are the next necessary coverage work.


## Generated-build review and streaming admission

- **Keep:** deterministic ladder, isolated Python oracle, immutable examples,
  source-bound tool receipts, one coordinator/vendor queue and independent TBs.
- **Improve (observed failures):** missing reset keys broke a real counter oracle;
  the startup prefix and explicit model protocol repair that boundary. A first
  malformed Python answer now gets one bounded retry with the actual diagnostic.
  Empty/unbounded examples stop before calls/allocations; provider/storage failures
  do not consume RTL repair attempts or appear as rejected designs.
- **Improve (demonstrated false positive):** scoreboard accepted a reset-gated
  combinational implementation under latency1. Track accepted transaction ages;
  matching a latency comment is insufficient. Actual simulator before/after logs
  retain this failure. Minimum age does not prove exact queue capacity/readiness.
- **Improve:** mutation qualification requires raw assertion detail plus a failure
  verdict; generic simulator failure, compilation, watchdogs and missing logs are
  insufficient. Independent counter/encoder controls and eight distinct faults
  have real expected verdicts. Streaming qualification remains a separate gate.
- **Maintain limits:** generated examples anchor Python, not separately injected
  temporal RTL sequences; generated startup reset does not establish reset kind or
  midstream reset. Independent queue tests check these properties for the new
  two-entry buffer. Read docs/GOLDEN_VERIFICATION.md before interpreting results.
- **Defer:** population search, new framework/provider and extra semantic roles.
  The measured need is stronger deterministic verification, not another model
  opinion. The next design adds state, capacity and backpressure with a bounded
  independent oracle; full UART/processor generation would outrun current evidence.


## Streaming feature review after measured failures

Keep both graders: generated Python/unit tests cover payload behavior, while an
independently qualified temporal TB checks exact capacity/readiness/reset and
all-output behavior. Same-byte capacity-one RTL passed the former and failed the
latter. The combined mode therefore gates child repair and every integrated
candidate, not only a manual check after choosing a winner.

Improve fault qualification with a bounded fixed portfolio. Retain the missed
readiness mutation; the payload grader detects stuck-zero and the independent
TB detects readiness. Changing a probe is not changing the grading testbench.
One observed assertion is minimum non-vacuity evidence; do not present it as
complete mutation coverage. Typed tool blockers now preserve infrastructure causes
and stop without RTL repair. No extra model judge, framework or agent layer was
needed to repair these boundaries. Keep population search deferred until these
checks have repeated model/budget-controlled results.


## Review after the completed streaming build

The combined loop produced a routed two-entry buffer (15 LUTs / 19 FFs) and its
saved winner passed the independent 893-cycle test. Retain this architecture:
payload-only qualification visibly missed readiness, so it cannot replace the
independent temporal grader. No additional role or framework is justified.

Two concrete repairs follow this experiment. Preserve raw assertion proof and
qualification reports through stage replay and completed-run integrity checks.
Reject the compiler's duplicate-module diagnostics before metrics or model review:
the real candidate had exit-zero overwrite warnings and was rejected only later.
The exact saved bad candidate now fails compilation before elaboration; unrelated
warnings remain accepted and infrastructure failures keep their classification.
These are deterministic guard repairs to the existing ladder, with fixture and
real-tool evidence, rather than a new verification mechanism.

Maintain source-frozen cohorts and honest failures. Next complexity should add a
parameterized synchronous FIFO and wraparound/full throughput tests, then a
packet-oriented block with explicit reset/backpressure rules. First complete the
fresh full tier0 merge gate. Defer extra search roles and framework changes until
controlled ablations demonstrate a benefit; no feature is removed merely because
one bounded optimization found no gain.


## FIFO01 recovery decision before implementation

FIFO01 atffc15fc passed generated and six-configuration independent verification,
then routed13LUT/6FF with setup-0.931ns and hold0.091ns. It is not timing closed.
The optimization candidate redeclared its frozen companion and was correctly
blocked before elaboration; this repeats the earlier streaming boundary mistake.
The run completed with an invalid-timing baseline retained, not a successful
physical result. Preserve the complete attempt and grader coverage misses.

Observed policy issues: generator/fix omitted immutable run/dependency evidence;
compile design failures skipped the candidate's repair opportunity; area-first
selection and strict objective comparison can block timing recovery. A controlled
old-policy reproduction using that real baseline and a synthetic14LUT timing-
feasible candidate confirms selection favors the invalid13LUT design. The14LUT
value is a synthetic policy test, not a physical measurement.

Implement the smallest corrections to the existing flow: explicit editable top
and frozen companion context for generator/repair/Doctor; one configured bounded
compile-or-simulation repair sequence with all verification rerun; one shared
feasibility-first comparison policy used in selection, promotion and rendered
contracts/evaluation. Recovery from known failed timing may increase area and
must be labeled timing recovery. Among timing-feasible designs the original
strict objective remains. Unknown timing cannot establish recovery. Keep actual
exit, RTL behavior, source identity, setup/hold and evaluator gates unchanged.
No new role/framework or unbounded retry is justified. Validate pure policy and
integrated failure/replay cases, fullsuite and fresh campaigns before main merge.


## Current FIFO recovery review

Keep generated payload and independent temporal graders: the exact same
readiness mutant passed one and failed the other. Preserve the miss, raw
assertions and source hashes. FIFO01 passed functionally but failed setup;
its 13 LUT / 6 FF result is a failed physical trial, not a published improvement.

Revise existing policy and feedback, without adding roles: feasibility-first
selection/promotion, explicit editable-top and frozen-companion context, and
configured bounded compile/simulation repairs with separate attempt evidence.
Keep strict objective improvement once timing is feasible. Explicitly label
recovery that increases area. Final source/TB/child identities must survive DONE
reuse; UTF-8 IO must be explicit on Windows. Before-failing regressions and
read-only review cover these repairs. Fresh live closure is still required.

The full regression run found one legacy synthetic cache fixture without its
required source/TB manifest (938 passes, one failure). Added truthful synthetic
lineage, retaining production guards and all assertions; its 20-test file passes.
The complete rerun passed **939 tests in349.85seconds** on frozen runtime.
Main remains gated on a fresh complete tier0 campaign.

After FIFO timing closure, the smallest next experiment is a packet-tagged FIFO:
store an end-of-packet bit with every beat and verify tuple alignment through
stalls, simultaneous transfers, wrap and reset. Reuse the current ladder and
dual graders. Defer parsing, CRC, store-and-forward, arbitration and CDC until
concrete failures justify that complexity. No new framework is justified.


## FIFO03 observed feedback corrections, before implementation

Source49599b5 reproduced baseline13LUT/6FF, setup-0.931ns/hold0.091ns.
Candidate1 closed neither setup(-0.905) nor its resource objective. Doctor's
masked read mux improved setup to-0.525 but remained invalid and was not adopted.
Candidate2 remained at-0.600. Its Doctor response exactly repeated source; the
remaining synthesis deadline expired and the trial ended budget_exhausted,
10calls,1200.654chargedtoolseconds/1349.068elapsed. No accepted FIFO gain.

Read-only review confirmed four existing feedback omissions. The first1800
report characters exclude real paths at line201+, and planner explicitly says
the path is unavailable. Rejected Doctor trials do not reach next planning.
The typed build spec's explicit invalid-payload qualifier is absent after
integration, so planner incorrectly requires matching empty output data.
Exact unchanged Doctor RTL also repeats the same measured flow unnecessarily.

Smallest correction: bounded report-hash-linked path excerpts; frozen complete
bounded resolved specification facts; labeled not-adopted Doctor advice in
existing evaluation/planner context; skip only proven source-and-flow-identical
surgery. Keep standalone optimization strict, all defined valid/stalled behavior
and reset/latency/interface/TB/exit/setup/hold gates intact. Do not mislabel hold
paths as setup or adopt merely less-negative slack. No new role/framework.
Oversized semantic metadata must fail explicitly rather than drop qualifiers.
Test missing/malformed/hold/routed precedence, exact hashes, actual prompts,
failed-trial visibility, no-op versus intentional physical changes, and replay.


## Feedback correction outcome before fresh physical trial

Keep the existing roles and gates. Final984tests passed423.26s; context51 and
Doctor74focused checks pass. Raw report/path/hash use one snapshot; full resolved
semantics are bounded without dropping qualifiers. Failed trial evidence and
source previews reach planning, while original related digests survive DONE.
No-op skip requires actual prior receipts/inputs and exact default-flow proof.

Remove test-only report inference: synthetic helper now has real path fields.
Do not infer data-net fanout from the selected path's clock-inclusive maximum.
Keep this metadata advisory; no new heuristic or driver parser was added.
Fresh physical FIFO and fulltier0 are still required. Unit results establish
these guard/feedback properties, not model robustness or timing closure.

## FIFO04 observed annotation-authority correction

Keep path excerpts, resolved semantics and rejected-trial feedback: actual
second planning used the Doctor trial path and generated a timing-feasible
candidate (24LUT/27FF, WNS0.318/WHS0.050ns). The harness nevertheless rejected it
solely for missing top latency annotation, despite known=false. Preserve this
failed outcome and its area tradeoff; no accepted FIFO closure follows.

Revise the ambiguous injected typed-build wording and explicit review rules.
Require the top header only when its authoritative declaration is known.
Retain typed metadata across validated complete transparent single-child wiring;
do not add graph latency inference, another model reviewer or manual regrading.
No verification, constraints or metric gates are relaxed.

Related review exposed a whole-file latency search that could borrow a helper
annotation or block-comment example. Keep one shared selected-module parser
for inference/client/four deterministic generation and repair gates. Preserve
original comments for static inference so malformed metadata is rejected as a
design issue, not raised after that boundary. The supported lexical subset and
no-top multi-module unknown result are explicit; no general Verilog elaborator
was added. Read-only final integration review found no blocker.

## FIFO05 measured feature decision

Keep exact path/spec evidence and top annotation authority: firstplan named real
RAMreadpath and requiredmatchingheader; allactualreviews passedlatencycriterion.
Keep separate generatedpayload and independenttemporal graders: payload again
missed readinessmutation, independent caughtit. Do not claim either provesall
parametercombinations. Keep boundedDoctor: toolonly-.016ns remainedrejected;
actualRTLrepair registered equivalentvalidstate and won22LUT/13FF,+.108/.076ns.
Firstfeasible24LUT shrank8.33%; initialinvalid13LUT is notanareasavingsbaseline.
Strict timing/objective policy retained priorvalidbest when an initialiter3
candidate failedsetup. No newrole/framework/threshold was needed.
ActualDONE nominal/child/spec/Doctorreport tests preserved327identities/budget.
No-op skip not exercised bythistrial; its regressions remain separate evidence.
BestofN1 is intentional boundedcost here; diversity/cache/weakmodel ablations
are not established by thisrun. Nextcomplexity packet-tagFIFO can reusetheflow
after freshfulltier0. Mainstillgated; fullsuite1074unchangedruntime.

## Fresh campaign07 and role boundaries

Complete tier0 passed2/2 on unchanged tested runtime. Counter review explicitly
accepted unknown numeric top latency as unknown (no invented annotation), and
accepted55→31LUT with positive setup/hold. Mux generated MUXF7/MUXF8 primitives
whose simulation libraries were not linked; xelab rejected them. One bounded
generator repair returned behavioral RTL, passed the ladder, and was correctly
rejected for no LUT gain. Keep the repair role and deterministic promotion gate.
Retain this library-support limit before claiming arbitrary vendor primitive/IP
coverage. Add a library adapter only when a required design establishes that
need, with actual primitive/control verification; no new agent role is needed.

Runtime roles remain planner, generator/repair, evaluator and Timing Doctor.
The harness owns contracts, source boundaries, execution, budgets and acceptance.
The development coordinator reviews and improves those mechanisms; bounded CLI
runs do not require this chat. Continuous unattended scheduling, provider quota
recovery and general hardware/application support remain separate capabilities.

## Packet fixture admission decision

Keep current multi-output scoreboard plus independent temporal checking. Adding
last as ordinary payload required no new engine or role. Supervised control
passed allsix selected configurations;19namedsource mutations failed actual
behavioralassertions. Retain bothtruncations as distinctimplementation probes,
but document overlappingobservablefaults ratherthan19independentclasses.
1105fulltests and60focusedtests passed; generatedgrader marker sensitivity is
still unmeasured. Measure its named faults before deciding whether runtime
qualification needs a change. No new feature justified by admission alone.

## Packet01 measured feature decision

Keep complementary graders: the generated grader detected six named marker
faults on the default instance but missed readinessflip; independent temporal
verification caught it. There is no observed missing multi-output comparison
to justify a new scoreboard engine or role. Keep report-grounded planning:
actual read-pointer/RAM-to-out_last path informed the first architecture change.
Keep bounded Doctor: tool settings closed timing at23LUT/31FF,+.078/.106ns;
subsequent failed/timing-feasible-but-larger trials remained rejected.

Cache reuse saved redundant candidate work, but duplicate proposals persisted
after the scheduled/stall replan, which also received the churn signal. Record this diversity limit. A future frozen,
equal-budget feedback/portfolio comparison can test improvement; this single
trial does not justify another agent or evolutionary framework. Existing
independent source review and331-identity DONE checks found no blocker; no
in-flight hard-kill or general parameter proof follows.

Fresh campaign08 passed2/2, matching cohort streak2/heldfalse. Counter gain
varied55→53 ratherthan prior55→31; retain both. A passing gate is not evidence
of repeatable optimization magnitude. Mux no-gain proposal correctly retained
baseline. Keep deterministic acceptance, comparable cohorts and failed trials.
No runtime modification was needed for the packet milestone.

## Divider admission: observed reset blind spot

Keep independent temporal checking plus compiling fault qualification. The
first admission correctly blocked model generation despite1175unit tests:
reset with ready1 let normal retirement hide an ignored reset. A coverage count
named reset_result did not establish stalled-result abort. Retain that case,
add ready0 reset and distinct mandatory coverage plus omission regressions.
Fresh21/21qualification and1180tests passed with unchanged reference/mutants.
No new runtime role or scoreboard engine was required. Carry this distinction
into future checker reviews; a scenario count alone is not fault sensitivity.

## Divider01 outcome and next necessary correction

The accepted sequential divider reduced38->26LUT (31.58%) and46->38FF with
positive setup/hold. Estimated power increased; do not claim power savings.
Keep report/contract-grounded planning: after one duplicate proposal, the next
plan's shared subtraction produced a useful distinct candidate. This differs
from packet01's repeated replan outcome; diversity reliability remains unproven.
Independent finalwinner and251-identity actualDONE checks passed.

Generated grader caught13/17applicablefaults but missed zero-divisor remainder
despite an explicit255/0example. Actual RTL stimulus had only0/0. Oracle example
qualification is separate from RTL input coverage. Revise scoreboard stimulus
to include eligible complete accepted-example payloads, retaining corner/random
cases and existing scheduling. Do not replay fixed-latency/stateful examples
as isolated transactions. Exact reset/readiness verification remains independent.
Original source/results archived before change; require a controlled unchanged
oracle/reference/mutant comparison and full regression before claiming closure.

Scoreboard payload correction validated:1226tests; same frozen oracle/reference/
fault reproduces oldzeroRmiss and newassertion, bothcontrolspass. Detection
13/17->14/17 without modelcalls,changedrandomtail orweakenedacceptance. Keep
the small deterministic payload selector. Keep independent temporal checker
for remainingreadiness/resetcoverage; no newengine orrole justified. Full
example timing/state replay and general mutation completeness remain unclaimed.

Fresh fulltier0campaign09 passed2/2 onnewruntime4618887;newcohortstreak1,
noheldtier.193testedidentities unchanged. Oldcohortstreaknotcarriedover.
User's product comparison requires matched empirical trials; generalagents
with identicaltools may matchorbeat current harness. Keep domain-specific
verification/measurement/evidence workflow, and measure usereffort and escaped
bugs before asserting an advantage. Rawunitcounts and selfbaseline PPA gains
do not establish superiority. No new role/framework is justified by that question.


## Previous-proposal study02: revise the default, retain the audit

Three chronological pairs on one divider did not reduce repeated proposals:
three repeats in each mode. One original baseline run hit quota; its separate
budget-preserving recovery is not an uninterrupted comparison. Token totals
are incomplete, model identity is unknown and host load was uncontrolled.
Keep immutable proposal evidence and bounded opt-in context; disable context
by default. Do not assert that context is harmful or generally ineffective.

The trajectory audit instead exposed stale instructions after a changed seed.
Supply the current RTL and bind each plan to its exact seed; the deterministic
binding is a correctness boundary, not a diversity guarantee. Keep verified
incumbents when fresh planning exceeds the original budget. Validate with
replay/budget tests and an actual changed-seed path before promotion.

The candidate audit separately reproduced a normalized-hash collision for
different Verilog string outputs. Exact UTF8 SHA256 dedupe is the smallest
safe correction. Cosmetic variants may now cost verification; normalized text
hashes remain advisory and cannot establish semantic equivalence. No cache
redesign, language parser, new model role or framework is justified.


## Source binding and exact dedupe: verified implementation decision

Keep seed-bound planning and exact dedupe:1,340 regression tests passed; a fresh
actual run exercised accepted-source replanning with no unbound generator input.
The exact winner independently passed six widths. Five restored tamper probes,
including the plan binding, were rejected with267 protected identities and no
new budget charges. Fresh full tier0 passed2/2 in a new cohort, streak1/heldfalse.

The live run was quota-interrupted, then recovered on unchanged source with
cumulative budgets. Its reporting observer also failed printing Unicode after
harness completion; that original exit/wall timing stays unknown. These results
validate the mechanism and evidence boundaries, not causal efficiency or
repetition improvements. Keep additional proposal context opt-in and retain
negative study results. No role/framework expansion is justified.


## Three-module dot-product design: keep composition and bounded repair

Independent checker admission detected all12 named compiling faults, including
hidden asynchronous partial-state reset. Three generated goldens and RTL modules
then composed correctly. A golden syntax error was repaired by the existing
bounded loop; no new role or parser is justified.

Keep the editable-top optimization boundary: equivalent logic can be inlined
while companion definitions stay frozen. This case mapped arithmetic into4DSPs,
reducing325→17LUT and52→18sliceFF. No hierarchical optimizer extension is needed
for this observed success. DSP internal registers are outside sliceFF counts;
total estimated power increased slightly. No general PPA benefit follows.

Revise the mechanical wrapper template: missing timescale triggered43-4099 only
when optimization compiled top before children. The same generated children/TB
reproduce that failure; addingonlytimescale passes685checks without modelcalls.
This is deterministic scaffold generation, so fix the template rather than spend
LLM repair budget. Preserve latency authority and severity policy; retain the
original completed run before integrating the tested patch.
