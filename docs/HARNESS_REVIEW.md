# Harness effectiveness review

Updated 2026-10-20. The objective is to make a bounded, reliable harness that
extracts useful work from weaker models. Design results are probes of that
system. No weaker-model performance has been demonstrated yet.

## What the latest experiments establish

- 436 regression tests passed. The counter32 reference checks every output and
  detects all four selected mutants in real Vivado simulation. Earlier nine
  generated-testbench cases cover positive and negative timing/streaming cases.
- Cohort tier0_fkxbmmwe originally finished 0/2 after worker exits, not failed
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
| Improve now | Report evidence delivered to roles | Supply timing as well as utilization report identities. Make parsed metric provenance explicit and bounded. A model should not have to guess which reports exist. |
| Improve now | Worker diagnostics and blocked outcomes | Nonzero exit currently discards diagnostics. Retain bounded error evidence and save an explicit resumable model-blocked outcome; never turn this into an RTL rejection. |
| Simplify next | Prose contract negotiation | Four successful calls preceded counter planning/generation. Build fixed optimize-mode contracts mechanically; spend model calls on architectural hypotheses and repairs. |
| Improve next | Acceptance policy | Define machine-checkable mandatory predicates and make model review advisory for their measurable portions. Preserve genuine semantic checks; add tests for any bug a reviewer finds. Do not simply bypass a rejection to publish a gain. |
| Improve | Legal mutation portfolio and Doctor | Suggestions must respect latency/reset constraints. Validate tool-only retiming, RTL surgery and hold-only failures separately. Candidate context must show actual tool settings. |
| Validate live | Contextual cache, build, golden process and restart | Regression coverage exists. This cohort does not prove live build, cache reuse, restart or general interruption recovery. Exercise each explicitly. |
| Measure | Best-of-N diversity, skills, watchdog and advisor | Current cohort uses N=1. Their marginal benefit has not been measured; do not present them as established gains. |
| Remove or disable clearly | Dead module-cache branch and unused controls | Build uses a disabled cache read branch while still writing entries. parallel_candidates has no execution consumer. Preserve config compatibility while rejecting unsupported settings or deleting dead branches with regression coverage. |
| Keep historical only | Legacy provider adapters and max_turns argument | Active runtime is Codex-only. max_turns is not enforced. Do not advertise these as working runtime capabilities. |

## Next feature coverage experiments

1. Finish recovery and archive the current cohort honestly. Keep original
   failed-attempt records separate from successful follow-up recovery.
2. Close report-provenance and worker-diagnostic gaps with regression tests.
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
