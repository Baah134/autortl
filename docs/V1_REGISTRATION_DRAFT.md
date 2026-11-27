# V1 false-acceptance experiment — registration DRAFT

**Status: DRAFT, not frozen, awaiting the owner's approval.** No V1 trial has
run, and none may run until the owner freezes this registration and its
decision rule. Every number, task and threshold below is a proposal. Freezing
means: wiring the prerequisites below (tested, committed), copying the final
task list and settings into a new evidence folder
(`evidence/<date>/v1-registration-01/`, like `final-registration-01`),
pinning the model, recording the runtime commit, and adding a dated
`docs/DECISIONS.md` entry with the rule.

Spec: `docs/ROADMAP.md` task V1. Mechanism: `docs/DESIGN.md` "Request
cross-check", `autortl/cross_check.py`. Failure mode:
`planner_spec_error_shared_by_oracle_and_rtl` (`data/taxonomy.yaml`).

## Question and hypothesis

The planner can misread the request (a reset that clears a register the
request never mentions; an input sampled one cycle early). The oracle,
generated testbench and RTL then all follow the misreading and the harness
accepts a wrong design. The request cross-check
(`spec_cross_check=request_traces`) has a second, independent call write cycle
traces from the request and port list only and runs them through the
qualified golden model before any RTL; a disagreement sends the spec back to
the planner once.

- **Hypothesis:** on tasks the harness was not developed on, the full harness
  with `request_traces` accepts fewer designs that fail the official testbench
  than the same harness with the check `off`, and passes at least as many
  tasks.
- **Null:** no difference in false acceptance, or fewer false acceptances only
  because correct designs are also lost.

## Fresh tasks only; final-02 tasks are a labelled "tuned" set

ROADMAP V1's older text proposes rerunning the final-02 false-acceptance
tasks. `docs/DECISIONS.md` (2026-11-21, twice) rules that out as evidence: the
cross-check, the SPEC_PROMPT clarification and two other fixes were designed
after reading final-02's failures, so any later number on those 40 tasks is
tuned on them. This draft follows DECISIONS:

- **Primary endpoint:** fresh tasks only (below). Only this set decides the
  default.
- **Tuned secondary set (descriptive, labelled "tuned"):** the tasks whose
  false acceptances were attributed to planner misreading: Prob066_edgecapture,
  Prob139_2013_q2bfsm, Prob070_ece241_2013_q2 (final-02) and Prob135_m2014_q6b
  (pilot-04, where the failure mode was first recorded). It shows whether the
  check catches the cases it was built from. It never enters the verdict and is
  reported beside, not inside, the primary result. Prob093 and Prob149 are left
  out: their references contradict their own prose
  (`official_reference_contradicts_request`), so a check that follows the
  request cannot change them. Prob027 (grader attribute) is a different cause.

## Arms

| Arm | Cell arm (proposed) | What runs | Budget per cell |
|---|---|---|---|
| C-off | `full` | `run.py build` as final-02 arm C (best-of-1, 1 iteration, out of context, `verification_policy=full`), `--spec-cross-check off` | 16 model calls, 1500 s tool, 2100 s wall (as final-02) |
| C-xcheck | `full_xcheck` | identical, `--spec-cross-check request_traces` | same caps |

Everything else is the same in both arms: runtime commit, pinned model
(`--model`, owner to name it), task prompts, budgets, Vivado version and part,
`max_fix_attempts`, and the grader compile check (proposed: off in both arms,
as in final-02; owner decision 5). The cross-check spends from the same
16-call cap and the shared `max_fix_attempts` counter, so a cell it pushes
over a cap counts against it; such cells are listed. No single-call arm:
the question is the check's effect inside the harness, and final-02 already
measured arm A.

Cells run trial-major through `benchmark.campaign`, both arms of a task
adjacent, so quota waits and host load fall on both arms alike. A cell is
attempted once and never rerun; grading starts only after every cell is
sealed.

## Prerequisites (code changes, described here, not made)

1. **Runner wiring.** `benchmark/pilot.py` does not set `spec_cross_check`
   (DECISIONS 2026-11-21, "Benchmark wiring is separate"). `full_command` and
   `run_full` need a `spec_cross_check` argument passed as
   `--spec-cross-check`; each registered cell declares it, and `run_full`
   refuses a cell whose arm and declared value disagree, as it already does
   for `verification_policy`.
2. **Arms in the campaign and report.** `benchmark/campaign.py`
   (`ARM_ORDER`) and `benchmark/report.py` (`ARMS`, paired comparisons) know
   only `single_call`, `ablation` and `full`. They need the `full_xcheck` arm
   and the paired comparison `full_xcheck` minus `full`.
3. **Rows carry the check's outcomes.** Every planner-written build records
   `spec_cross_check: {policy, checks}` in its run summary; the graded rows
   need the per-cell outcome (`agree`, `replanned`, `disagreement_kept`,
   `repairs_exhausted`, `skipped`, `unusable`, `traces_incompatible`,
   `no_comparable_rows`, `golden_error`) so the report can count them.
4. **Decision rule as code.** A module like `benchmark/claim.py` (proposed
   `benchmark/v1_claim.py`) with the thresholds below as constants and pytest
   fixtures, committed before the first cell, applied by `benchmark.finish`.
5. **Smoke run before freezing.** One trial of each arm on two pilot tasks
   (proposed Prob038_count15 and Prob107_fsm1s; already seen, so outside every
   claim) to confirm the flag reaches the run, the records appear and the
   per-cell cost is near the estimate. Archived as a smoke check, not a result.

`pilot.py`, `campaign.py` and `report.py` are no-edit zones while any
campaign runs (AGENTS.md).

## Tasks (proposed)

VerilogEval spec-to-RTL, dataset commit
`c498220d0a52248f8e3fdffe279075215bde2da6`, the adjudicated catalog
`benchmark/catalogs/verilogeval-c498220.json` (156 tasks, 106 families).

**Rule (deterministic, declared before any trial):**

1. *Seen tasks:* the 40 final-02 tasks
   (`evidence/2026-11-21/final-02-results/benchmark_registration.json`) and the
   6 pilot tasks (Prob036_ringer, Prob033_ece241_2014_q1c, Prob147_circuit10,
   Prob038_count15, Prob135_m2014_q6b, Prob107_fsm1s). These are every task
   any arm has run on in this project (flash-01/02/03 used the final-02 40).
2. *Exclude every family containing a seen task* (46 families), so no
   near-duplicate of a tuned task enters, and the four broken references in
   `benchmark/catalogs/exclusions_c498220.json`. Eligible: 93 tasks in 59
   families (32 combinational logic, 3 combinational arithmetic,
   15 sequential, 9 FSM).
3. *Weight toward sequential behaviour:* take **all** 15 sequential and all
   9 FSM families (the failure mode is reset and cycle timing) and all
   3 arithmetic families, plus the 13 best-ranked combinational-logic families
   (combinational tasks check that the check does not hurt designs it cannot
   help; Prob070 was combinational). 40 tasks, 60% sequential or FSM against
   40% in final-02.
4. *Rank:* families and tasks by SHA-256 of
   `autortl-v1-fresh|<commit>|<name>` (ties by name); each family contributes
   its best-ranked task. The salt is new, so the draw is independent of the
   final-02 ranking.

Selection logic (run from the repository root; standard library only):

```python
import hashlib, json
COMMIT = "c498220d0a52248f8e3fdffe279075215bde2da6"
SALT = "autortl-v1-fresh"
CATS = ("combinational_logic", "combinational_arithmetic", "sequential", "fsm_control")
QUOTA = {"combinational_logic": 13}  # other categories: every eligible family
rank = lambda name: hashlib.sha256(f"{SALT}|{COMMIT}|{name}".encode()).hexdigest()

catalog = json.load(open("benchmark/catalogs/verilogeval-c498220.json"))
exclusions = json.load(open("benchmark/catalogs/exclusions_c498220.json"))
reg = json.load(open("evidence/2026-11-21/final-02-results/benchmark_registration.json"))
pilot = ["Prob036_ringer", "Prob033_ece241_2014_q1c", "Prob147_circuit10",
         "Prob038_count15", "Prob135_m2014_q6b", "Prob107_fsm1s"]
seen = {t["id"] for t in reg["tasks"]} | set(pilot)
barred = {catalog[t]["family"] for t in seen}
fams = {}
for task, e in sorted(catalog.items()):
    if e["family"] not in barred and task not in exclusions:
        fams.setdefault(e["family"], (e["category"], []))[1].append(task)
selected = []
for c in CATS:
    ranked = sorted((f for f in fams if fams[f][0] == c), key=lambda f: (rank(f), f))
    for f in ranked[:QUOTA.get(c, len(ranked))]:
        selected.append({"task": min(fams[f][1], key=lambda t: (rank(t), t)),
                         "category": c, "family": f})
canonical = json.dumps(selected, sort_keys=True, separators=(",", ":"))
print(len(selected), hashlib.sha256(canonical.encode()).hexdigest())
```

Output: 40 tasks, selection sha256
`28bbd3e8e1fe141cca89bb970ff13dc574367aca8baef84a03d0d0cfb5e77df7`.

| Category | n | Tasks (rank order) |
|---|---|---|
| sequential | 15 | Prob060_m2014_q4k, Prob058_alwaysblock2, Prob068_countbcd, Prob117_circuit9, Prob084_ece241_2013_q12, Prob054_edgedetect, Prob080_timer, Prob105_rotate100, Prob098_circuit7, Prob118_history_shift, Prob040_count10, Prob034_dff8, Prob145_circuit8, Prob085_shift4, Prob104_mt2015_muxdff |
| fsm_control | 9 | Prob143_fsm_onehot, Prob095_review2015_fsmshift, Prob154_fsm_ps2data, Prob140_fsm_hdlc, Prob079_fsm3onehot, Prob155_lemmings4, Prob110_fsm2, Prob074_ece241_2014_q4, Prob129_ece241_2013_q8 |
| combinational_logic | 13 | Prob130_circuit5, Prob113_2012_q1g, Prob103_circuit2, Prob017_mux2to1v, Prob004_vector2, Prob008_m2014_q4h, Prob112_always_case2, Prob114_bugs_case, Prob003_step_one, Prob026_alwaysblock1, Prob094_gatesv, Prob116_m2014_q3, Prob064_vector3 |
| combinational_arithmetic | 3 | Prob016_m2014_q4j, Prob024_hadd, Prob009_popcount3 |

Disclosure: Prob040_count10 shares a family with Prob035_count1to10, one of
the four grader-control tasks of `evidence/2026-11-14/pilot-grader-controls-01`
(official reference and hand-made mutants only, no model output), so it is not
a seen task under rule 1. The other three control tasks are already excluded.

The whole fresh pool is small: after this draw only 19 combinational-logic
families remain unseen, and no sequential or FSM ones. A later fresh
experiment on VerilogEval would have to use those 19 or another dataset.

## Trials

Three trials per task and arm (240 primary cells), as in final-02. With
clustered data the number of tasks, not trials, limits the interval, so
extra trials buy little. Tuned set: five trials per task and arm (40 cells),
as ROADMAP V1 proposed; descriptive only.

## Endpoints

All intervals: 95% task-clustered percentile bootstrap, 10,000 resamples,
seed 20261115 (`benchmark/report.py` `cluster_bootstrap`), over tasks with
at least one evaluable cell in both arms. Cells stopped by infrastructure are
excluded from rates; missing submissions count as failures (as final-02).

**Primary: false-acceptance difference.** Per task and arm, FA_t = cells
internally accepted and failing the official testbench (upstream-compatible
verdict) divided by evaluable cells. Endpoint: mean over tasks of
FA_t(C-xcheck) − FA_t(C-off). Per evaluable cell, not per accepted cell, so
every task has a value in both arms and the pairing holds; the usual rate
over accepted designs (as in final-02's table) is reported beside it.

**Secondary:**

1. *Upstream pass-rate difference*, C-xcheck − C-off, same bootstrap: the
   check must not block correct designs.
2. *Blocked tasks:* tasks where C-off passes every evaluable trial and
   C-xcheck passes none, with a `replanned` or `disagreement_kept` outcome in
   a C-xcheck cell. Named, with each cell.
3. *Added model calls:* calls per cell and per pass in each arm, the ratio,
   and cells that hit the 16-call or wall cap.
4. *Check outcomes:* counts of every outcome per arm cell, including
   `disagreement_kept` (the planner kept its spec after a second
   disagreement) and the share of cells where the check ran (not `skipped`).
5. *Replans that changed the verdict:* `replanned` cells that pass upstream
   (fixed) or fail on a task where C-off passed at least once (possibly
   broken), named.
6. Tuned set: the same tables, labelled "tuned on final-02/pilot tasks".

## Decision rule (proposal)

Applied in order by the decision module; constants as stated.

1. **Completeness:** more than 10% of either arm's cells stopped by
   infrastructure → `inconclusive`, descriptive only.
2. **Harm:** pass-rate interval entirely below 0 → `blocks_correct_designs`.
   Default stays `off`.
3. **Harm:** false-acceptance interval entirely above 0 →
   `increases_false_acceptance`. Default stays `off`.
4. **Events:** C-off has false acceptances on fewer than 3 tasks →
   `insufficient_events`: the fresh tasks did not show the failure mode often
   enough to measure a reduction. Descriptive; default stays `off`.
5. **Adopt:** false-acceptance interval entirely below 0, **and** pass-rate
   interval lower bound ≥ −10 pp, **and** mean pass-rate difference ≥ 0,
   **and** no blocked task → `reduces_false_acceptance`.
6. **No difference:** false-acceptance interval inside ±3 pp and pass-rate
   interval inside ±10 pp → `no_material_difference`. Default stays `off`.
7. Otherwise → `inconclusive`. Default stays `off`.

**When the default may change.** Only on `reduces_false_acceptance` (ROADMAP V1
acceptance: false acceptances fall without blocking correct designs), and then
by a new dated DECISIONS entry and an owner-approved change of the
`RunConfig.spec_cross_check` default; the verdict alone changes no code. Every
verdict updates the taxonomy repair text from "open/unmeasured" to the measured
outcome. The ±10 pp pass-rate margin is the one final-02 used; the ±3 pp
false-acceptance margin is about two thirds of the target-mode rate final-02
showed.

**Not allowed:** removing tasks or cells after the first trial, rerunning a
cell, changing a threshold after grading, or moving tuned-set numbers into the
primary result. A later change needs a new dated decision with the original
verdict reported beside it.

## Power and size: the likely result is inconclusive

False acceptances are rare and clustered. final-02 arm C accepted 110 designs
and 11 failed upstream (10%), but only 5 of those 11 are the failure mode the
check targets (Prob066 ×3, Prob139 ×2; Prob070's one was in arm B). Five come
from two tasks with contradictory references and one from a grader attribute,
which the check cannot change. So the target rate is about 5% of accepted
cells, on 2 of 40 tasks (3 of 40 counting arm B). Two of those were sequential
or FSM tasks out of 16 (12%); with 24 such tasks here, about 2 to 4 affected
tasks are expected, if fresh tasks resemble final-02.

The bootstrap resamples tasks, so the effective sample is the handful of
affected tasks. A simulation of this design (40 tasks, 3 trials, affected
tasks failing in two of three trials, a 2% background false-acceptance rate
in both arms, 300 replicates) gives the probability that the false-acceptance
interval falls entirely below 0:

| Affected tasks (of 40) | Check removes all | Removes 75% | Removes 50% |
|---|---|---|---|
| 2 | 0.14 | 0.10 | 0.09 |
| 3 | 0.26 | 0.18 | 0.14 |
| 4 | 0.47 | 0.31 | 0.20 |
| 6 | 0.81 | 0.61 | 0.31 |
| 8 | 0.96 | 0.80 | 0.48 |

(Scratch simulation, 2,000 resamples per replicate; not part of the
registration. It ignores the event minimum of rule 4, which would turn the
2-task rows into `insufficient_events`.)

Read plainly: about 80% power needs a complete effect on about six affected
tasks, or a 75% effect on about eight. With the 2 to 4 affected tasks
expected, power is 14 to 47% even if the check removes every target false
acceptance. The most likely verdicts are `insufficient_events` or
`inconclusive`. That is an acceptable, publishable
outcome: it says the check is not shown to help and the default stays off.
Larger sizes are limited by the fresh pool (no unseen sequential or FSM
families remain), so more power needs another dataset (for example RTLLM,
already surveyed for B3) under a separate registration.

## Budget estimate

From final-02 arm C (`summary.json`, 120 cells): 6.6 model calls, 5.4 min wall
and 3.6 min Vivado tool time per cell (sequential and FSM cells: 5.8 calls,
4.9 min, 3.4 min). The check adds 1 call per planner-written generated-oracle
build (2 if the first answer is unusable) and, on a disagreement, 1 planner
call plus a rebuild (about 5 calls). Assuming disagreements on 10 to 25% of
cells, C-xcheck costs about 8 to 9 calls per cell.

| Set | Cells | Codex calls | Vivado tool hours | Wall hours (excluding quota waits) |
|---|---|---|---|---|
| Primary, C-off | 120 | ~790 | ~7 | ~11 |
| Primary, C-xcheck | 120 | ~1,000–1,100 | ~8 | ~12 |
| Tuned, both arms | 40 | ~300 | ~2.5 | ~4 |
| Smoke (pilot tasks) | 4 | ~30 | ~0.3 | ~0.5 |
| **Total** | **284** | **~2,100–2,250** | **~18** | **~28** |

ROADMAP R3 puts the Codex window at about 58 final-02 cells (about 4.8 calls
each, so roughly 280 calls). The total is therefore about 8 usage windows,
several days with waits. One Vivado job runs at a time, so the run blocks B3
and other implementation work while it lasts. Token use was about 160,000
input tokens per harness cell in final-02, roughly 45 million in total.

## Open decisions for the owner

1. **Pinned model** for both arms (final-02 ran the unobserved CLI default;
   V1 should pin a name with `--model`).
2. **Task source:** approve the fresh VerilogEval rule and list above, or name
   another source (RTLLM, a harder subset).
3. **Quota:** approve about 2,100–2,250 Codex calls and about 28 hours of
   runtime, and when to spend them relative to B3.
4. **Thresholds:** the ±3 pp false-acceptance margin, the −10 pp pass-rate
   floor, the 3-task event minimum and the 10% infrastructure limit.
5. **Grader compile check** (`--grader-check`): off in both arms (as final-02,
   proposed) or on in both (removes the Prob027-style cause from both arms).
6. **Tuned set:** keep it (40 extra cells, descriptive) or drop it.

## Limits known now

- Fresh means "not run by any arm in this project", not "unseen by the
  model": public tasks do not exclude training contamination.
- The SPEC_PROMPT clarification made after final-02 is in both arms, so V1
  cannot measure it separately, and C-off here is not the final-02 harness.
- The check runs only on single-module fixed-latency specs with a generated
  oracle; multi-module and scoreboard specs are `skipped`, and an interface
  misreading is outside it.
- One model, one dataset, functional correctness only.
