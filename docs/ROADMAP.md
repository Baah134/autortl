# AutoRTL roadmap — the working plan for any agent

Written November 15, 2026 from `docs/REVIEW_2026-11-15.md`. This file replaces
`docs/archive/ACTION_PLAN.md` as the plan of record (that file stays as history). Update
task status here when a task's acceptance criteria are met; put history in
`docs/PROGRESS.md`, never here.

**Goal.** A public, reproducible FPGA/EDA portfolio project whose front page
makes three claims and proves each one: (1) generated cores work on real
hardware, (2) its verifiers are themselves tested, (3) a registered comparison
shows what the harness does and does not add over a single model call.

**Definition of done.** A stranger can clone the repository, read a README of
about 150 lines, run the offline demo and the test suite, open a benchmark
report with intervals, and find every number bound to committed evidence. A
tagged release exists on `main` with a licence.

## 1. How to work here (read once)

1. Arrival: `git status`, `git log --oneline -5`, `python scripts/session.py status`,
   `python coordination/mail.py inbox --for <codex|claude>`. If another
   coordinator is active, stay read-only. Otherwise `python scripts/session.py
   start --owner "<you>"`, claim exact file scopes with `claim-task`, and keep
   the lease alive with `python scripts/lease_keeper.py --token-file <file>`
   (section 3).
2. Hard rules (from CLAUDE.md and DESIGN.md): the spec is law; model output
   lands only in `.v`/`.py`/spec JSON; Vivado severities are promoted only;
   infrastructure failures never count as design verdicts; every parser has a
   pytest with a fixture; **every new failure mode gets a `data/taxonomy.yaml`
   entry before its fix**.
3. Never weaken a contract, verifier, metric gate or test to make something
   pass. A result you do not like is still the result.
4. **While a benchmark campaign is running, do not edit `autortl/`, `llm/`,
   `data/`, `.claude/skills/`, `run.py`, `benchmark/pilot.py` or
   `benchmark/verilogeval.py`.** Each cell launches the checkout's code and
   records its runtime identity. New files elsewhere are safe. Code changes go
   in a git worktree created with `git worktree add .claude/worktrees/<name>
   -b <name> <commit>` and are merged after the campaign.
5. A spent attempt is never rerun or edited. Fix, commit, freeze a new
   manifest, start a new attempt directory, and record the old one as aborted.
6. Before committing: focused tests for what you touched, then the full suites
   (section 3). Stage explicit paths, never `git add .`. Commit only what you
   verified. Push and merges to `main` need the owner's approval.
7. Evidence: one folder per result under `evidence/<date>/<name>/` with a
   README, the raw data and `archive-manifest.json` (file name to SHA-256 of
   LF-normalised bytes). No home-directory paths or personal data in committed
   files. `python tools/evidence_audit.py --rev HEAD` must pass.

## 2. Current state (November 15, 2026)

- Branch `codex/contract-context`, local commits ahead of `origin` (not
  pushed). `main` frozen at `ca61dbc`.
- Harness: all suites green at the last full run (2,287 harness, 323 tooling).
- Benchmark machinery is complete and tested: `benchmark/verilogeval.py`
  (dataset, selection, grader), `pilot.py` (arms A/B/C), `registration.py`
  (final selection), `campaign.py` (runner), `report.py` (grading gate and
  statistics). Runbook: `docs/BENCHMARK_PILOT.md`.
- Pilot gate passed (pilot-06: 6/6 in all three arms). Final registration
  frozen: 40 tasks, `evidence/2026-11-14/final-registration-01`.
- `final-01` was aborted after 5 cells (`empty_netlist_unplaceable`, fixed).
  **Final comparison `final-02` is running** (360 cells, runtime `7731a66d2`)
  from `C:/Users/prince.baah/autortl-private/final-02` via
  `python -m benchmark.campaign`. Progress: `final-02/campaign.log`. See task B1.

## 3. Environment facts (this machine)

| Thing | Value |
|---|---|
| Python with pytest/pyyaml | a venv; create with `python -m venv <dir>` and `pip install -r requirements.txt` (no system interpreter has pytest) |
| Vivado | `C:/AMDDesignTools/2025.2/Vivado/bin` (2025.2); `run.py doctor` resolves `.bat` paths |
| Codex CLI | set `AUTORTL_CODEX_BIN` to `%LOCALAPPDATA%/OpenAI/Codex/bin/<hash>/codex.exe`; `python run.py doctor` must print "ready" |
| Icarus Verilog 12.0 | `C:/msys64/ucrt64/bin/{iverilog,vvp}.exe`; or set `AUTORTL_IVERILOG`/`AUTORTL_VVP` |
| VerilogEval | `C:/Users/prince.baah/autortl-private/verilog-eval` at `c498220d0a52248f8e3fdffe279075215bde2da6`, folder `dataset_spec-to-rtl` |
| Benchmark attempts | `C:/Users/prince.baah/autortl-private/<attempt>/` (outside the repository, never model-visible) |

Commands:

```bash
python -m pytest tests/ -q -p no:cacheprovider                      # harness, about 15 min
python -m pytest coordination hardware/basys3/harness_winners/tests hardware/basys3/fmax/tests tools/tests -q -p no:cacheprovider
python tools/evidence_audit.py --rev HEAD                           # committed evidence hashes
python run.py doctor                                                # environment check
python scripts/demo.py                                              # offline walkthrough, no model or Vivado
python scripts/lease_keeper.py --token-file <file> [--stop-file <file>]   # renew the lease every 10 min
```

The machine must not sleep during a campaign (lid open, mains power). Sleep
stalls Vivado and model calls; the harness recovers, but hours are lost.

## 4. Tasks

Status: `todo`, `doing`, `done`, `blocked(<by>)`. Do them in the order of
section 5 unless the owner says otherwise. Each task lists its acceptance
criteria; a task is not done until all are met and committed.

### Track B — the registered comparison

**B1. Finish, grade and report `final-02`** — `doing` (campaign running)
- Watch: `tail final-02/campaign.log`. A `stop` event with reason `model blocked`
  means Codex quota or login: wait for quota, then restart the same command
  (cells with an output directory are skipped; the one blocked cell stays
  sealed `model_blocked` and is reported as missing). `3 consecutive
  interrupted cells` means infrastructure: diagnose before restarting.
- Restart command (skips existing cells):
  `python -m benchmark.campaign --manifest <final-02>/manifest.json --dataset <D> --attempt <final-02>`.
- When the log's last event has reason `all cells attempted`:
  1. `python -m benchmark.report grade --manifest <final-02>/manifest.json --dataset <D> --attempt <final-02> --iverilog C:/msys64/ucrt64/bin/iverilog.exe --vvp C:/msys64/ucrt64/bin/vvp.exe`
  2. `python -m benchmark.report render --summary <final-02>/grades/summary.json --catalog benchmark/catalogs/verilogeval-c498220.json --title "VerilogEval spec-to-RTL: single call vs AutoRTL (40 tasks x 3 trials)" --out <scratch>/report.md`
  3. Archive to `evidence/<date>/final-02-results/`: `report.md`, `report.json`,
     `summary.json`, `manifest.json`, `runtime-identity.txt`, the run log, a
     `cells.json` (per cell: run record without the command, verdict, run
     summary status) and the sealed RTL. Replace home paths with `<home>`
     (see `evidence/2026-11-14/pilot-06-results-01` for the layout). Write a
     README stating identity, protocol, the tables, every false acceptance by
     task, every non-`done` termination and the limits.
  4. Read every false-acceptance and every harness-fail/single-pass task; add a
     taxonomy entry for each new cause (after the campaign, rule 4).
- Acceptance: all 360 cells sealed and graded once; report committed with
  intervals, paired differences, false-acceptance rate and cost; audit passes;
  no cell rerun; README (task P3) quotes only numbers from this report.

**B2. Decide the claim from the data** — `blocked(B1)`
- If C beats A with an interval excluding 0: state it with the interval. If
  not: state that on these tasks one call is as good at a fraction of the
  cost, and that the harness's measured value is in B3/B4 and on hardware.
  Record the decision in `docs/DECISIONS.md`. No post-hoc task removal.

**B3. Optimisation benchmark (where the harness should differ)** — `todo`
- Question: on designs that are functionally correct in both arms, does the
  harness produce smaller or faster routed designs than a single call?
- Design: take tasks from B1 where arm A and arm C both pass in at least one
  trial and the design has at least 20 LUTs after synthesis (so there is
  something to optimise); add 8 to 12 larger public designs (RTLLM v2.1 with a
  pinned commit; check each licence and that its reference passes its own
  test, as in `evidence/2026-11-14/pilot-grader-controls-01`).
  Arms: A = single call; C-opt = `run.py build` with `--iterations 5
  --best-of-n 4`. Both graded for function first; then both synthesised with
  the same out-of-context flow, part and period (`autortl.vivado.run_synthesis`),
  recording LUT, FF, WNS, WHS. Report paired LUT ratio and timing closure only
  for pairs where both are functionally correct. Pin the model with `--model`.
- Needs: `benchmark/ppa.py` (synthesise a sealed submission, parse metrics,
  refuse a failing design) with tests on fixture reports; a registration file;
  the same campaign/report flow.
- Acceptance: registered before any trial; report with paired ratios and
  intervals; evidence folder; taxonomy entries for new failures.

**B4. External-task tier in the curriculum** — `todo`
- Add `curriculum/tier_ext/` with the six pilot tasks as build entries (prompt
  as the spec request, the official test only as the held-out grader through
  `benchmark.pilot`). Purpose: regressions like F4 are caught by the normal
  gate. Acceptance: documented entry format, a runner test with doubles, and
  one recorded live pass of the tier.

### Track V — verification research

**V1. Measure and reduce false acceptance** — `todo`
- Baseline: the false-acceptance rate and cells from B1.
- Mitigation to test (one, measured): *independent example derivation*. A
  second planner call, given only the original request (not the first spec),
  produces input/output examples; the build fails spec lint with a dispute if
  the golden model built from the first spec disagrees with them. The existing
  dispute path (`spec_disputes`, DESIGN.md "Disputed examples") is the hook.
  Implement behind a recorded config field (like `verification_policy`), off
  by default until measured.
- Experiment: rerun the B1 false-acceptance tasks plus Prob135_m2014_q6b, 5
  trials each, with and without the mitigation; report false acceptances,
  added calls and any true designs wrongly blocked.
- Acceptance: taxonomy entry updated from "open" to the measured outcome;
  default changed only if false acceptances fall without blocking correct
  designs.

### Track P — publication

**P1. Licence** — `done` (November 15): MIT, owner-approved; `LICENSE`, README
section, VerilogEval attribution kept in `tests/fixtures/verilogeval/README.md`.

**P2. Push and integrate** — `doing`: branch push approved and done November 15;
remaining (owner approval needed for the merge):
confirm CI is green (`.github/workflows/tests.yml`: harness, evidence audit,
tooling); open a PR to `main`. The release gate in START_HERE applies: full
suites, evidence audit, and the final re-hold the owner decides on.

**P3. README rewrite** — structure `done` (November 15, 149 lines); numbers `blocked(B1)`
- Target about 150 lines: one-sentence pitch; a results table with three rows
  (hardware, verifier qualification, benchmark) each linking to evidence; the
  loop diagram; 10-line quick start (`doctor`, `demo.py`, one `build`); what
  the harness guarantees; honest limits; links to DESIGN, BENCHMARK_PILOT,
  the report and case studies. Move the long tables to `docs/RESULTS.md`.
- Acceptance: every number has an evidence link; no claim the report does not
  support; the offline demo command in the README runs.

**P4. Demo recording** — `blocked(owner)`: a two-minute screen and board
recording of one build and the UART echo. Board access needs the owner's
explicit authorisation (no JTAG/programming by agents without it).

**P5. Release** — `blocked(P1,P2,P3)`: tag `v1.0.0` on `main` with release
notes drawn from PROGRESS; attach the benchmark report.

### Track D — documentation and process

**D1. One agent guide** — `done` (November 15): merge START_HERE, AGENTS, CLAUDE, GEMINI and
AGENT_HANDOFF into `AGENTS.md` (rules, arrival, lease, departure) of at most
150 lines. Keep `CLAUDE.md` and `GEMINI.md` as three-line pointers so each
tool still finds its file. `START_HERE.md` becomes a pointer to AGENTS.md,
this roadmap and SESSION_HANDOFF. Acceptance: no rule lost (check each hard
rule and lease rule survives), no duplicated paragraph across the files.

**D2. Single current checkpoint** — `done` (November 15): rewrite `docs/SESSION_HANDOFF.md`
to one current section of at most 60 lines; move the stacked "Earlier" and
"Paused" sections to PROGRESS (the Codex candidate-export stage stays recorded
as parked, with its path). Acceptance: one `## Current` heading.

**D3. DESIGN.md without dated notes** — `todo`: move the dated sections
("November7 ...", "November8 ...") into `docs/DECISIONS.md`, leaving DESIGN as
the timeless architecture. Add the benchmark architecture (arms, sealing,
grading gate) as a section. Acceptance: no month names in DESIGN headings.

**D4. TASKS.md archive** — `done` (November 15; the whole file is archived, this roadmap is the task board): move completed acceptance records to
`docs/archive/TASKS-2026.md`; TASKS keeps only open items and points here.

**D5. Lease ergonomics** — `done` (keeper script) / `todo` (duration): the
lease lapsed five times on November 14. `scripts/lease_keeper.py` renews it.
Still to do: make the default lease 4 hours in `scripts/session.py`
(`coordination` tests must cover it) so a sleeping machine does not drop it.

### Track C — code health (after B1; these touch the harness)

**C1. Split `_run_optimize`** — `todo`: extract baseline, iteration, selection,
doctor and finish phases into methods or a small `optimize/` package, with no
behaviour change. Acceptance: full suites unchanged, byte-identical run
summaries on the recorded FSM tests, no function over 120 lines in `fsm.py`.

**C2. Public interfaces** — `todo`: export `doctor.resolve_tool` and
`artifacts.validate_manifest`; stop importing private names in `benchmark/`.

**C3. Tooling** — `todo`: `pyproject.toml` (ruff with a small rule set, no
reformat of history), pinned `requirements.txt`, CI Python matched to
development (3.12 or 3.14, one of them), a `ruff check` CI job. Acceptance:
CI green, no behaviour change.

**C4. Planner prompt for external requests** — `todo`: from B1 failures, add
only general guidance (never task-specific). Each change needs the failing
run as a fixture and a taxonomy entry.

**C5. Evidence weight** — `todo`: document `git sparse-checkout` for a
code-only clone in the README; measure checkout time before and after. Do not
rewrite history.

### Track H — hardware (owner-gated)

**H1.** Run two B1/B3 winners on the Basys 3 through the existing board shell
flow (`hardware/basys3/harness_winners`), 50,000 transactions against an
independent model. Needs explicit owner authorisation for board access.

## 5. Order of work

1. B1 (running) — do not disturb it. In parallel, only safe-file work: D1, D2,
   D3, D4, P3 structure, B3 design and `benchmark/ppa.py` in a worktree.
2. When B1 is sealed: grade, report, archive, B2 decision, then P3 numbers.
3. Owner decisions: P1 licence, P2 push/PR, P4 recording, H1 board.
4. Merge worktree work, then C1 to C5 and B4.
5. V1, then B3 (both use the same campaign machinery and a pinned model).
6. P5 release.

## 6. Risks and how to handle them

| Risk | Handling |
|---|---|
| Codex quota ends mid-campaign | The runner stops at the first `model_blocked` cell; restart the same command later |
| Machine sleeps | Harness retries infra failures; keep the lid open; check `Get-WinEvent` Kernel-Power 42/107 if a cell takes hours |
| A harness bug appears mid-campaign | Do not patch the checkout. Let the campaign finish, report the failures, fix afterwards, and say so in the report |
| Ceiling results (all arms near 100%) | Report them; the answer to "does it add value" then comes from B3 and V1 |
| Lease lapses | `python scripts/session.py start` again and reclaim scopes; nobody else may have claimed (check `status` first) |
| Vivado crash banner | Classified as infra; rerun is safe; add a taxonomy entry if the trigger is new |

## 7. Open decisions for the owner

1. PR and merge to `main` (P2). 2. (done: licence, branch push.) 3. Whether B3 uses RTLLM, a
harder VerilogEval subset, or the project's own tier 4 to 6 designs. 4. Pinned
model name for B3/V1. 5. Board authorisation (H1, P4).
