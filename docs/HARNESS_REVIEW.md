# Harness effectiveness review

Updated 2026-10-20. The objective is to make a bounded, reliable harness that
extracts useful work from weaker models. Design results are probes of that
system. No weaker-model performance has been demonstrated yet.

## What the latest experiments establish

- 497 regression tests passed at the repaired implementation. The counter32 reference checks every output and
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
| Improve now | Report evidence delivered to roles | Implemented timing/utilization/power manifests, file hashes, bounded previews and explicit metric provenance; fresh live evaluation next. |
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
