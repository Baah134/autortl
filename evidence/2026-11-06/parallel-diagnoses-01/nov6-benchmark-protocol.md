# Proposed public benchmark protocol — November 6, 2026

Status: independent planning artifact for docs/ACTION_PLAN.md, not a registered
experiment or completed benchmark. No dataset snapshot, task IDs, model trials,
adapter implementation or tool qualification was produced in this task. Current
runtime remains frozen; this document does not authorize interrupting signoff.

## Decision and primary-source basis

Use **40 VerilogEval specification-to-RTL tasks, six disjoint pilot tasks, three
trials per task and three arms**: 360 scored runs, plus separately costed pilot
work. Do not blend RTLLM and VerilogEval scores into one headline.

The authors' [VerilogEval repository](https://github.com/NVlabs/verilog-eval)
distinguishes the original code-completion release from its specification-to-RTL
format and documents Icarus v12; v13 development is unsupported. Use the latter
task format consistently. Its [license](https://github.com/NVlabs/verilog-eval/blob/main/LICENSE)
is MIT; retain notices and provenance.

[RTLLM's official repository](https://github.com/hkust-zhiyao/RTLLM) reports 50
designs in v2.0 and description/test corrections in v2.1. Its README also retains
older 29-design text: version names alone are insufficient dataset identity.
[File_list.md](https://github.com/hkust-zhiyao/RTLLM/blob/main/File_list.md)
includes asynchronous FIFO and clock-generation tasks, making an indiscriminate
port to AutoRTL's current contract risky. Its documented simulation flow uses
VCS; porting that grader is additional work. It is also
[MIT licensed](https://github.com/hkust-zhiyao/RTLLM/blob/main/LICENSE).
Recommendation: reserve RTLLM for a separately preregistered larger-design/PPA
study after this functional comparison. Do not transplant published performance
numbers across revisions, models, tools or target technologies.

## Freeze tasks before observing model results

1. Resolve the selected upstream revision to a full 40-character commit and
   archive it with license, upstream URL and retrieval date. Do not run against
   mutable main. Record SHA256 of every prompt, test, reference and grading file.
   Pin Icarus v12 build, Python/dependencies, OS/container image and time limits.
2. Inventory all spec-to-RTL IDs at that revision. Two reviewers classify using
   only task statements/interfaces: combinational logic, combinational
   arithmetic, sequential datapath/state, and FSM/control. Assign exactly one
   category per task using that precedence rule documented in the manifest.
   Group obvious related task families so pilot and final sets are family-disjoint.
3. Exclude only predefined technical incompatibilities: unavailable/legal
   dependencies, irreconcilable statement/interface ambiguity, unsupported
   semantics requiring alteration of the task, or broken official reference
   controls. Publish every excluded ID/reason and the full eligible denominator.
   Hard tasks, wide signals, previous model failures and suspected low success
   are not exclusions. Missing adapter support is a disclosed scope restriction.
4. Before generation, rank eligible family IDs by SHA256 of
   `autortl-public-v1|upstream_commit|family_id`; select six pilot tasks with
   category coverage and exclude their entire families from final selection.
   Select 40 final tasks proportionally across remaining categories using
   largest-remainder quotas and the same hash ranking (ID lexical tie-break).
   Include all members of a selected family only if that rule is frozen in
   advance; otherwise choose its lowest-ranked task. Retain family labels.
5. If fewer than 40 supported, independent-family tasks remain, register the
   actual size only if at least 30; otherwise stop and choose another protocol.
   Do not replenish tasks after seeing results. Review reference/grader controls
   before finalizing the roster, then publish the exact IDs and exclusion table.
6. Pilot only: test adaptation, extraction, grading, timeout/cancellation,
   accepted/rejected statuses and accounting. Tune prompts/budgets on pilot only.
   Freeze the final runtime/adapter/prompts/manifest after pilot. A discovered
   final-set defect requires a versioned amendment and complete affected-cell
   reruns retained alongside originals, not selective replacement of failures.

Task selection cannot be claimed complete until the SHA, IDs, categories,
family policy, licenses and exclusion log are actually populated and reviewed.

## Three arms and the estimand

| Arm | Generation and feedback | Acceptance recorded before hidden grading |
|---|---|---|
| A: one model invocation | Same immutable task/interface; one backend invocation, no repair feedback or role calls | A nonempty extracted candidate is submitted, not described as internally verified |
| B: qualification ablation | Same bounded AutoRTL loop as C, but generated-TB mutation qualification is skipped | Existing remaining internal gates decide acceptance; bypass is an explicit experimental receipt |
| C: full | Full released AutoRTL workflow, including generated oracle/TB checks and mutation qualification | Normal internal acceptance, with candidate hash and evidence |

B removes **one** safeguard, not a moving bundle of planner, evaluator and
verification changes. Keep internal simulation, immutable inputs, real process
exit proof, budgets, interface checks, isolation and final grader in all relevant
arms. There is currently no supported CLI flag for this ablation; implement and
review a narrow experiment seam after the live freeze ends. Never ship it enabled
by default or infer an ablation from `--generate-golden` being absent.

All arms receive the same source task statement, interface and any deterministic
contract conversion. Generated planning/verification consumes B/C budgets. No
arm receives the official test/reference, hidden-grader outputs, or another
arm's candidates. Do **not** pass the official grader as `build --tb`: that
would feed final-test feedback into generation. Generate internal verification
from public specification alone; preserve all internal verifier failures.

Each arm returns one predeclared final candidate: accepted incumbent if one
exists, otherwise latest complete candidate, otherwise missing. Store internal
acceptance separately. External success on that candidate is the primary
functional endpoint even if AutoRTL rejected it internally; report the
accepted-and-external-pass endpoint separately. Do not cherry-pick the best
candidate using the hidden tests or choose among three trials after grading.

This measures bounded workflows versus one invocation, not identical-compute
methods or superiority to a general coding agent. A tools-enabled agent baseline
would be a separate experiment. Codex CLI is itself a worker, not necessarily
one underlying inference; name A 'one backend invocation' when using that backend.

## Independent final grader and controls

Use the pinned official test/reference and grading semantics for every arm.
The upstream [Makefile](https://github.com/NVlabs/verilog-eval/blob/main/Makefile.in)
compiles candidate, test and reference using Icarus with top `tb`, and bounds
simulation at 30 seconds. Its
[analysis script](https://github.com/NVlabs/verilog-eval/blob/main/scripts/sv-iv-analyze)
provides the upstream result interpretation. Preserve that classification and
add separately recorded real compile/simulation exits, timeout and provenance;
never infer success from a generated 'TEST PASSED' string or make exit alone.

The adapter must validate official filenames/top and expected completion for
each pinned task. No parser API or Windows portability is assumed yet. Verify
the adapter against the unmodified official workflow on pilot controls. Run the
official reference as a positive control plus independently chosen behavioral
faults, syntax failures and hanging candidates as negatives. Controls diagnose
grader coverage, not prove complete correctness. Freeze strengthened tests, if
any, before trials and report their score separately from official compatibility.

Final-grader files live outside model-visible mounts/workspaces. Disable network
and restrict filesystem access for generation and simulation; simulator inputs
are untrusted executable content. A prompt telling the worker not to use tools
is not enforcement. The present Codex read-only temporary working directory does
not alone establish hidden-grader isolation. Resolve this before trials, through
an approved restricted execution environment or an already available bounded
text-only endpoint; do not provision a new paid provider without authorization.

Never send hidden failures back for repairs. Grade all runs only after their
final artifact/acceptance receipts are sealed. Any post-hoc diagnosis is clearly
separated from the frozen primary result.

## Budgets, repetitions and accounting

Provisional pilot ceilings: A one attempted model invocation; B/C each 16
attempted invocations, N=1, three optimization iterations, 25 tool minutes,
35 active wall minutes and one infrastructure retry. A also has the same
35-minute outer wall ceiling, but its normal backend request timeout remains
identical to B/C's per-call timeout. These are proposals, not newly run budgets.
Freeze final ceilings after pilot and before final IDs are generated against.
Charge planning, oracle, review, repair, rejected proposals and retries.

Use one pinned model/backend/configuration for all roles/arms; record requested
and observed model identity, backend version, reasoning/sampling options,
context limits, system instructions, worker tool permissions and response size
policy. Do not claim controlled temperature/seed settings that the backend does
not expose. A default alias with unknown resolved model prevents a controlled
model-strength claim. Three fresh sessions per task are repeated trials, not
guaranteed statistically independent samples from a stable model distribution.

Use a frozen randomized block schedule across task/trial/arm to reduce temporal
service drift. No shared conversation, proposal cache or learned memory between
trials; no cross-arm incumbent reuse. Record task family, schedule position and
timestamps. Avoid parallel vendor contention or measure concurrency explicitly.

Report successful and failed-call input/output/cached tokens when supplied,
missing-usage counts, total backend calls, elapsed model/tool/active wall time,
timeouts, quota/network/storage interruptions and human intervention minutes.
Unknown tokens or dollar cost are null/unknown, never zero. Price estimates need
dated tariffs and are distinct from billed cost; subscriptions are not free
inference. Keep observed cost distributions and success-versus-cost plots.
B/C share ceilings, not necessarily actual spend; A has deliberately less
compute. Optional fixed-budget repeated-single-call comparison needs a fourth
predeclared arm and a candidate-selection rule, not retrospective best-of-N.

Every planned cell remains in the completion table. Report infrastructure
failures separately and provide end-to-end completion over all planned cells;
do not silently drop them from a conditional functional rate. Retries keep
their original attempt records and charged budget. Runtime/model changes start
a new cohort; pause/resume never resets a spent budget.

## Analysis and claims

Primary: mean of per-task externally passing trial fractions, with per-task
three-trial results. Paired B–C and A–C differences use task-cluster bootstrap
confidence intervals (10,000 resamples, fixed analysis seed); preserve all arms
and three repeats together when resampling. Related families warrant family
cluster sensitivity analysis. Do not treat 120 trials as 120 independent tasks.
With 40 tasks/three repeats, intervals may be wide: publish them and all failures.

For B/C report false acceptance as internal-accept AND external-fail divided by
internal-accept, plus its raw count over all trials. Zero acceptances means
undefined conditional rate, not zero. Report accepted/pass, accepted/fail,
rejected/pass, rejected/fail and missing/infra cells. A's submission failure
rate is useful but is not the same as a verifier's false-acceptance rate.

Register C–B functional improvement as the primary hypothesis; all other
comparisons descriptive unless multiplicity is handled in advance. Keep the
qualification mechanism if it improves measured acceptance reliability at a
declared cost; null/negative results remain publishable. Do not convert tiny
point differences into superiority claims when paired intervals span zero.

Public benchmarks can be present in training data. No statement of contamination
freedom, unseen-problem generalization, or formal equivalence follows. Report
verbatim-reference similarity as diagnostic only; it neither proves nor rules
out memorization. A future private, independently authored holdout is separate.

Routed FPGA PPA is secondary: only externally correct candidates under identical
device, clock, implementation mode, I/O constraints and tool revision. Report
LUT/FF/DSP/BRAM/power jointly with failures and matched-task coverage. Functional
results must not disappear because timing or synthesis failed. Do not compare
PPA only on differing survivor sets without a paired subset report.

## Minimal adapter and existing code touchpoints

Propose one experiment-only Python adapter plus tests and manifest schema, not
a new agent framework. Its responsibilities: load frozen task IDs; make explicit
typed-contract conversions; isolate each arm/trial; invoke an arm; seal final
candidate/status; independently grade; append immutable result records; summarize.
Do not use `curriculum.runner` hold/promotion statistics as public benchmark scores.

Existing implementation inspected November6:

- `run.py`: build/optimize/resume/bench, model and budget flags, independent TB,
  generated golden, exact output directory, out-of-context mode. No public-dataset,
  functional-only, hidden-grader or ablation CLI exists. Build's full PPA gates
  mean its DONE status is not the external functional endpoint.
- `autortl.spec`, `autortl.linter`, `autortl.verilog_interface`: deterministic
  schema, wrapper and interface checks; conversion must not invent clock/reset,
  latency, parameters or signedness. Probe representability on pilot.
- `autortl.fsm`: generated oracle/TB path and `_qualify_source` are the narrow
  review points for B/C; do not monkeypatch live modules. Preserve a versioned
  experimental diff/config and receipts proving which qualification gate ran.
- `llm.client.ask(role, prompt, system='', budget=None, route_override=None,
  max_turns=1, model=None)` exists; attempted calls are charged before dispatch,
  retries occur for some failures, and router_stats.jsonl records metadata.
  A must enforce one attempted invocation, including retries, and retain failed
  responses. The client's recorder currently writes alongside package code:
  isolated copies or a reviewed per-run sink are needed, not canonical writes.
- Available built-ins are Codex CLI and OpenAI-compatible HTTP; named endpoints
  can route to other configured backends. Availability/authentication is not
  implied by source support. Codex metadata may leave model/cost/usage unknown;
  max_turns is not a guaranteed hard worker-turn cap.
- `autortl.budget` tracks tokens for accounting, not a hard token cap; reconcile
  router failures and missing usage rather than trusting success-only totals.
  `autortl.state` atomic writes/events and frozen inputs provide useful provenance
  patterns. Keep grader evidence separate from internal acceptance evidence.

## Verified command outline — do not execute as public trials yet

These are existing CLI shapes, checked against run.py, with placeholder paths
and model values to be populated only after pilot and protocol freeze:

```powershell
python run.py doctor
python run.py build --spec prepared/task/design_spec.json --generate-golden --model BACKEND.MODEL --implementation out_of_context --iterations 3 --best-of-n 1 --max-llm-calls 16 --max-vivado-minutes 25 --max-wall-minutes 35 --max-infra-retries 1 --output-dir runs/task/trial-1/full
python run.py resume --run runs/task/trial-1/full
```

The build example intentionally does not supply the official test as --tb.
It is not a complete public benchmark command: deterministic conversion, A/B
arm implementation, final-candidate export, isolation and independent grading
still need reviewed code. No invented `--ablate`, `--dataset` or `--seed` flags.
For the upstream Linux grader, verified compile shape from its Makefile is
`iverilog -Wall -Winfloop -Wno-timescale -g2012 -s tb -o sample candidate.sv TASK_test.sv TASK_ref.sv`.
Use actual pinned filenames and preserve the official simulation timeout and
analysis semantics in the adapter; this is not yet a validated Windows runner.

Next approval artifact: populated dataset/selection manifest plus pilot adapter
tests and raw control receipts. Only then freeze and schedule the 360 final runs.
