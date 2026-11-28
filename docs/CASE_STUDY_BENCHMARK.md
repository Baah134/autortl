# Case study: a registered comparison the harness lost

AutoRTL was compared with a single model call on 40 public VerilogEval
spec-to-RTL tasks, three trials each, graded by the official testbench. The
single call passed **94.1%** and the full harness **86.1%** (difference
−9.2 percentage points, 95% CI −19.2 to −0.8). The harness used **7.4 times**
the model calls per pass, and about **10%** of the designs it accepted failed
the official testbench. The decision rule was fixed before grading, so the
verdict is `single_call_better` and is reported as run.

| Arm | Passed | Rate | 95% CI | Model calls per pass | Wall hours |
|---|---:|---:|---|---:|---:|
| A: single call | 111/118 | 94.1% | 86.7 to 100.0 | 1.1 | 0.2 |
| B: harness without generated-testbench mutation qualification | 100/118 | 84.7% | 74.2 to 93.3 | 8.1 | 10.6 |
| C: full harness | 99/115 | 86.1% | 73.3 to 94.2 | 8.0 | 10.7 |

Pass counts are over graded cells; cells stopped by infrastructure are
excluded (see below). Source: the
[final-02 results](../evidence/2026-11-21/final-02-results/README.md), which
are generated from the sealed cells.

## Why it was registered before grading

A harness can look good when its authors choose the tasks, the baseline and
the endpoint afterwards. The comparison fixed those choices first:

- **Tasks.** [The registration](../evidence/2026-11-14/final-registration-01/README.md)
  was frozen after the pilot gate and before any final trial. It selects 40
  tasks from 144 eligible (99 families) of an adjudicated 156-task catalog,
  by category quota (21 combinational logic, 3 arithmetic, 10 sequential, 6
  FSM) and by SHA-256 rank of the family name. Families containing a pilot
  task were excluded. Four tasks with broken official references were removed
  before selection (three whose testbench watchdog fires on the reference, one
  port mismatch).
- **Grading.** Only after all 360 cells were sealed, once, with the
  official testbench under Icarus Verilog 12 and the pinned upstream analyzer.
  A cell is attempted once and never rerun.
- **Decision rule.** [Registered November 20](DECISIONS.md) and implemented as
  [`benchmark/claim.py`](../benchmark/claim.py). The published sentence is that
  module's output, not a hand-written summary.

One timing detail: the tasks and protocol were registered November 14, but the
decision rule was registered November 20 with 123 of 360 cells already sealed.
It still preceded any grade, because the grading command refuses to run until
every cell is sealed. An earlier attempt (final-01) was stopped after 5 of 360
cells for a harness defect on wiring-only designs; those cells are retained and
not reported.

## The three arms

- **A, single call.** One model call with the task's public prompt. The
  extracted module is submitted unverified. No tools, no retries.
- **B, ablation.** The harness without mutation qualification of its generated
  testbenches. It isolates whether that gate matters.
- **C, full harness.** `run.py build` with the planner, generated oracle and
  testbench, verification ladder and Vivado flow. Optimization was set to its
  minimum (one iteration, best-of-1, out of context) because VerilogEval grades
  function only. A cell without an accepted design counts as a failure.

All arms received identical prompt bytes. The official testbench and reference
were never shown to a model or passed as a testbench. The pilots
([runbook](BENCHMARK_PILOT.md)) validated the adapter, grader and budgets on
six other tasks and are never pooled with the final cells. They also found
defects that were fixed before the final run, such as a metrics gate that
stopped combinational designs with no clock.

## The decision rule

Primary endpoint: official-testbench pass. Primary comparison: arm C minus
arm A, as the mean of per-task differences with a 95% task-clustered bootstrap
interval over the 40 tasks.

- Interval above 0: `harness_better`. Below 0: `single_call_better`. Inside
  ±10 pp: `no_material_difference`. Otherwise `inconclusive`.
- If more than 10% of any arm's cells were stopped by infrastructure, the
  verdict is downgraded to `inconclusive`.
- Every internally accepted design that fails the official testbench is
  named. Above 5% of an arm's accepted designs, the claim must say internal
  acceptance is not a reliable correctness signal.
- C minus B, B minus A, calls per pass and every non-`done` termination are
  always reported. Removing tasks or cells, rerunning cells and changing a
  threshold after grading are not allowed.

## Infrastructure stops

Some cells end for reasons that say nothing about the design: the model quota
ran out (`model_blocked`) or the process was interrupted. A stop is not a
verdict, so it is excluded from rates and listed: 2 cells of arm A, 2 of B and
5 of C, all under the 10% limit, so the verdict was not downgraded.

A cell where the harness itself reported failure (`failed`) is different. It
counts as a failure, because the harness did not deliver a design. That is 8
cells of B and 5 of C. Excluding both kinds would hide real losses;
counting infrastructure stops as failures would punish designs that were never
judged. The same principle runs through the harness: infrastructure failures
never mutate a design and never count as fix attempts.

## Why the harness lost

The gap is not spread across tasks. Per-task differences, harness minus
single call, from [summary.json](../evidence/2026-11-21/final-02-results/summary.json)
(passes over evaluable cells):

| Task | Single call | Full harness | Contribution to −9.2 pp |
|---|---:|---:|---:|
| Prob066_edgecapture | 3/3 | 0/3 | −2.5 |
| Prob139_2013_q2bfsm | 3/3 | 0/2 | −2.5 |
| Prob131_mt2015_q4 | 3/3 | 0/3 | −2.5 |
| Prob153_gshare | 3/3 | 1/3 | −1.7 |
| Prob027_fadd | 3/3 | 2/3 | −0.8 |
| Prob078_dualedge | 2/3 | 3/3 | +0.8 |

The other 34 tasks are equal. The contributions sum to −9.2 pp.

**Prose-to-spec translation errors shared by oracle and RTL.** The harness first
rewrites the request into a typed spec. Its oracle, generated testbench and RTL
are then all derived from that spec, so a spec error passes every internal
check. On two tasks the planner added or moved behavior the request never
stated:

- *Prob066_edgecapture.* The planner added that reset also clears the
  previous-input register. The request does not say so and the reference does
  not do it, so the first edge after reset is lost: 91 of 266 samples
  mismatched in all three full cells. All three were internally accepted. The
  single call passed 3/3.
- *Prob139_2013_q2bfsm.* The planner sampled `x` on the edge that clears `f`,
  one cycle before the reference, so `g` rises a cycle early: 198 of 1,002
  samples mismatched in both graded full cells, both internally accepted. The
  single call passed 3/3.

The pilot had already shown this failure once: on Prob135_m2014_q6b the
planner misderived a state table and arm C accepted a design that mismatched
the official test on 6 of 100 samples, while arm A passed. It was recorded as
`planner_spec_error_shared_by_oracle_and_rtl` and left open. B and C were
indistinguishable overall (+0.4 pp, CI −5.0 to +5.8), so mutation
qualification of generated testbenches is not what separates the harness from
a single call.

**Builds that ended without a design.** Prob131 got a multi-module plan with no
trusted integration testbench; every module was generated and verified, and
then the build stopped (`multi_module_plan_without_trusted_tb`, 0/3 for both
harness arms). On Prob153 the golden model returned post-edge outputs at
latency 0, and two of three full cells failed
(`fixed_latency_observation_ambiguous`). These are harness defects, not
translation errors. Together they account for 4.2 pp, against 5.0 pp for
Prob066 and Prob139.

## What was not a harness fault

- **Prob093 and Prob149: the official reference contradicts the request.**
  The reference's `mux_in[2] = ~d` disagrees with the Karnaugh map at `cd=11`
  in Prob093; in Prob149 the prose says the output rises with the level and the
  reference does the opposite. Every arm fails them, the single call with
  identical mismatch counts (11 of 60, and 1,171 of 2,040). The harness arms
  followed the prose and accepted, so these two tasks produce 5 of arm C's 11
  false acceptances. Following the stated request is correct, so there is no
  harness change, and the tasks stay in the denominator
  (`official_reference_contradicts_request`).
- **Prob027_fadd: a grader compatibility failure.** One full cell put a Vivado
  `LUTNM` attribute before a continuous assign. Vivado accepts it; the
  Icarus-based grader stops with `Invalid module item`, so a correct design was
  graded `compile_error`. The registered verdict is kept
  (`grader_rejects_vendor_attribute`).

The 11 false acceptances in arm C therefore split as 5 planner errors
(Prob066 ×3, Prob139 ×2), 5 reference contradictions (Prob093 ×3, Prob149 ×2)
and 1 grader rejection. The rate is 11 of 110 accepted designs (10.0%; arm B
10 of 110, 9.1%). Both are above the registered 5% limit, so the claim states that internal
acceptance is not a reliable correctness signal on these tasks. The rule fixed
that reading before grading; it is not adjusted for the cases that are not the
harness's fault.

## What changed afterwards, and why the number did not

After grading, each cause above was entered in `data/taxonomy.yaml` and fixed or
mitigated where the cause was the harness's:

- the planner prompt now forbids behavior the request does not state, says
  reset clears only what the request says it clears, and keeps the request's
  own timing words beside the derived rule;
- the planner spec-repair loop rejects a multi-module plan when no trusted
  testbench is supplied, and a supplied multi-module spec without one fails at
  lint;
- the golden-model prompt now states that latency-0 outputs come from the state
  at the start of the step, before the update.

None of these is counted in the result. The Prob131 and Prob153 fixes were
written on a separate branch while final-02 ran and merged only after it
finished. Under the [November 21 decision](DECISIONS.md), final-02 is reported
as run, no cell is rerun with the fixes, and any later number on the same 40
tasks is tuned on them and is reported beside the registered one, never in
place of it. The
planner-prompt mitigation is also untested live; its effect has to be measured
on tasks outside final-02. The two reference contradictions and the grader
compatibility case need no harness change.

## What it implies

The result measures one backend (the Codex CLI default, whose model was not
reported), public tasks that may be in its training data, functional
correctness only, and a single-call arm that is one invocation, not a
tools-enabled agent. On short single-module tasks with a well-written prose
request, the extra planning and verification layers added cost (about 8 calls
and 10.7 hours against 1.1 calls and 0.2 hours) and, through the spec
translation step, new ways to be wrong, without a measured gain in
correctness.

It does not show the harness fails where it was built to help. The
[twelve board-verified cores](../README.md) and the optimization results in
[RESULTS](RESULTS.md) (for example AES-128 from 9,108 to 614 LUTs) come from
tasks with a trusted contract, an independent checker and a routed-design
metric to improve. Those runs have no single-call baseline, so they do not
show that the harness beats one. That comparison is the next experiment,
[ROADMAP B3](ROADMAP.md): on designs that both arms get functionally right,
compare routed LUTs and timing between a single call and the harness with five
iterations and best-of-four, registered before any trial. In parallel, measure
and reduce false acceptance on tasks outside final-02, for example by deriving
examples a second time from the original request. This benchmark gives that
work a baseline: 10.0% false acceptance, and 94.1% for a single call.
