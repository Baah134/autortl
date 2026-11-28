# How AutoRTL works: a guided tour of the code

This tour follows one `optimize` run from the command line to a verified
winner, then covers build mode, crash-safe resume and the hardware suite. Each
step points to the code that does it, by file and function, class or
constant name, so you can open it and read it. It also answers the questions people ask most about the design.
[DESIGN.md](DESIGN.md) explains the intent; this document shows where that
intent lives in the code.

## The idea in one paragraph

A language model is good at proposing RTL and bad at knowing whether it is
correct. So the model is used only as a proposal function. Everything that
decides is deterministic and lives in the harness:

- the contract the design must keep
- the testbench, which must first prove it can catch bugs
- the Vivado flow and its message severities
- the metrics, which must pass integrity checks
- the selection rule

The model cannot touch any of them. A candidate that breaks the contract is
rejected, not negotiated with.

## Map of the code

| Area | File | Responsibility |
|---|---|---|
| CLI | `run.py` | `optimize`, `build`, `resume`, `bench` and `doctor` subcommands (the `sub.add_parser` calls) |
| Orchestrator | `autortl/fsm.py` | The run loop, stage journal and verification ladder (`class Orchestrator`) |
| Contract | `autortl/contract_context.py` | Renders the fixed, hash-bound optimization contract (`run_evidence`, `render_fixed_optimize_contract`) |
| Candidates | `autortl/bestofn.py` | Mutation portfolio, exact-source dedupe, deterministic selection |
| Static checks | `autortl/static_checks.py`, `autortl/verilog_interface.py` | Ports, widths, signedness and declared latency, checked before any tool runs |
| Tools | `autortl/vivado.py` | xvlog/xelab/xsim and synthesis from fixed TCL templates |
| Testbenches | `autortl/tbgen.py` | Generated fixed-latency and scoreboard testbenches |
| Qualification | `autortl/tbqual.py` | A testbench must fail sabotaged designs before it can grade |
| Golden models | `autortl/golden.py`, `autortl/golden_worker.py` | Generated Python oracles, qualified against the spec's examples |
| Failure triage | `autortl/triage.py` | Infrastructure vs design vs unknown |
| Message taxonomy | `autortl/taxonomy.py`, `data/taxonomy.yaml` | Vivado message IDs, repair hints, severity promotion |
| Metrics gate | `autortl/metrics_gate.py` | Implausible metrics are an infrastructure error, never a score |
| Budget | `autortl/budget.py` | Model-call, tool-time and wall-time limits; degrades best-of-N |
| Timing doctor | `autortl/timing_doctor.py` | Tool options first, RTL surgery second, replan last |
| State | `autortl/state.py`, `autortl/cache.py` | Atomic checkpoints, events, metrics cache |
| Model backend | `llm/backends/codex_cli.py`, `llm/routing.yaml` | One sandboxed Codex CLI call per role invocation |

## One optimize run, step by step

**1. Freeze the inputs and the harness itself.** `Orchestrator._prepare_inputs`
in `fsm.py` does two things:

- It hashes every harness source file into `runtime.json`.
- It copies the design, testbench and spec into the run folder with their
  hashes.

On resume, a changed harness file or input aborts the run, so a result can
never be silently regraded by different code (the `runtime.json` and
`inputs.json` checks in `_prepare_inputs`).

**2. Verify the baseline.** `Orchestrator._run_optimize` refuses to
optimize without a testbench. The original design goes through the full flow:
compile, simulate, synthesize, place and route (`_full_flow`). Then two gates
check the result:

- The metrics gate rejects impossible numbers. A LUT total of zero or a
  missing WNS raises `MetricsGateError` (`metrics_gate.py`, `validate`).
- Tool exit receipts must also pass (`fsm.py`, `_process_exit_gate`).

**3. Freeze the contract.** The harness collects facts it measured itself:

- source and testbench SHA-256
- part and clock period
- baseline metrics and declared latency
- constraints and report hashes

It renders them into a contract (`contract_context.py`, `run_evidence` and
`render_fixed_optimize_contract`, called from `_run_optimize`). The model sees
this contract but cannot edit it. If the contract on disk ever differs from the
re-rendered one, `_run_optimize` stops the run.

**4. Plan.** When needed, the planner role writes a plan (the
`allow_replan` decision in `_run_optimize`). It is bound to the hash of the
exact design it was written for (the `plan_binding` evidence), and a plan for a
different seed stops the run (`planning_stop`).

**5. Generate best-of-N candidates.** Each candidate comes from a different
mutation prompt for the objective (`bestofn.py`, `mutation_prompts`). `dedupe`
drops byte-identical sources (`bestofn.py`, `dedupe`), so the same design is never paid for
twice.

**6. Climb the verification ladder** (`Orchestrator._verify_optimization_candidate`
in `fsm.py`). Each rung is cheaper than the next, so most bad candidates die
in milliseconds:

1. Static check of ports, widths and signedness (`static_checks.check`). Then
   *spec is law*: a declared `@latency` that differs from the contract is a
   failure, not a negotiation.
2. `xvlog` compile (`vivado.xvlog_check`, through `_tool`).
3. Simulation against the qualified testbench (`vivado.xsim_run`).

A design failure gets a bounded number of repair attempts. Each repair prompt
carries the taxonomy's hint for the Vivado message IDs found
(`Taxonomy.repair_instruction`). Every repaired answer re-enters the ladder from rung 1. An
infrastructure failure leaves the candidate *unverified*: it never triggers a
repair and never changes the RTL (the `kind != FailureKind.DESIGN` branch).

**7. Synthesize survivors** (rung 5 in `_run_optimize`). A cached result is
reused only if it is still for the same source, testbench and tool context
(`_cache_context`), and if it passes the metrics gate again.

**8. Select deterministically** (`bestofn.py`, `select`). Candidates are sorted
by:

1. rungs passed
2. timing feasibility
3. the objective metric
4. a secondary metric for ties, when every feasible candidate reports it
5. source length

So a design that meets timing always beats a smaller one that doesn't.

**9. Repeat** until the iteration count or the budget runs out. As the budget
shrinks, best-of-N degrades from N to 2 to 1, and replanning stops below 30%
remaining (`Budget.effective_best_of_n`, `Budget.allow_replan`). The budget can
only be charged, never refunded (`Budget.charge_llm`, `Budget.charge_vivado`).

## The invariants, and where each is enforced

| Invariant | Where |
|---|---|
| Spec is law (interface, latency) | `fsm.py` `_verify_optimization_candidate`; contract re-render check in `_run_optimize` |
| Model text never reaches TCL or a shell | Paths are sanitized for TCL (`vivado.py`, `_tcl_path`); TCL comes only from templates (the `vivado.py` module docstring); the model runs in a read-only sandbox (`codex_cli.py`, `ask`) |
| Severities are promoted, never demoted | `promotion_tcl` emits only `-new_severity ERROR` (`vivado.py`) |
| Infrastructure failures never mutate the design or count as attempts | Classifier `triage.classify`; ladder `fsm.py` `_verify_optimization_candidate`; journal keeps infrastructure outcomes uncommitted so a resume retries them (`Orchestrator._stage`) |
| A testbench must catch bugs before it grades | `tbqual.qualification_mutations` builds an operator mutant plus stuck-at-0 and stuck-at-1 stubs; `Orchestrator._qualify_source` requires a retained assertion failure |
| Metrics must be plausible | `metrics_gate.validate` |
| Results cannot be silently regraded | Runtime and input freezing, `Orchestrator._prepare_inputs` |
| A testbench never grades a stale child | A candidate that stops instantiating a companion the trusted testbench tests directly is rejected before any tool runs (`Orchestrator._boundary_violation`, `companions.violation`) |
| A locked checkpoint is infrastructure, not a crash | `CheckpointLockedError` (`state.py`) keeps the old checkpoint intact; `run.py` reports `infra_blocked` and the run resumes |

## How the testbenches work

`tbgen.generate` picks one of two compare modes from the
spec:

- **Fixed latency** (`generate_fixed_latency_tb`): it drives one stimulus per cycle and
  compares each output `latency` cycles later.
- **Scoreboard** (`generate_scoreboard_tb`), for valid/ready designs. It:
  - applies periodic backpressure on `out_ready`
  - inserts input bubbles that carry changing invalid data
  - holds the producer stable while blocked
  - adds off-edge reset pulses for synchronous-reset contracts
  - checks that `out_valid` never drops and the output stays stable while
    stalled
  - checks that no result appears before the minimum transfer latency
  - checks that the scoreboard drains exactly

Expected values come from the Python golden model under the same reset
initialization as the RTL driver (`tbgen.expected_outputs`).

## Build mode

`Orchestrator._run_build` in `fsm.py` turns a typed spec into a design:

1. Lint the spec (`linter.lint_spec`). A spec the planner wrote from a prose
   request gets its lint or load errors back for a bounded repair; a supplied
   JSON spec is law and fails at once.
2. Elaborate stub modules, so a broken blueprint fails before any generation
   (`linter.write_stub_project`).
3. Generate and verify each module in turn against its own qualified
   testbench (`Orchestrator._build_module`).
4. Write the top level mechanically, with no model involved
   (`linter.top_verilog`).

The result then becomes the baseline for optimize mode.

## Crash-safe resume: the stage journal

Every model call, tool run and decision goes through
`Orchestrator._stage`:

- Each stage gets a deterministic identity: scope, category, name and an
  occurrence index.
- A completed stage saves its result and its artifact hashes
  in `completed.json`.
- On replay, a completed stage returns its saved result instead of running
  again, and its artifacts must still match their hashes.
  This is why `resume` costs no extra model calls for finished work.
- Infrastructure failures are deliberately not committed, so the next resume
  retries them.

The tool wrapper `Orchestrator._tool` does two more things:

- It charges tool time to the budget and caps each timeout at the time
  remaining.
- For simulation, it records the exact verified inputs and refuses a replay
  if they changed (`verification_inputs.log`).

## The model call

`ask` in `codex_cli.py` runs `codex exec --sandbox read-only --ephemeral --json` in
a fresh temporary directory, with the prompt on stdin. A timeout kills the
worker's whole process tree; on Windows that is `taskkill /T /F`
(`_terminate_worker`). No API key is involved; it uses your existing Codex
login. The role-to-model routing lives in `llm/routing.yaml`.

## On real hardware

`hardware/basys3/harness_winners` is the part built by hand around the
harness's output. Every winner runs unedited on a Basys 3 behind a generic
UART shell, checked against independent models. See its
[README](../hardware/basys3/harness_winners/README.md) for:

- the LFSR traffic shaper, and why correlated LFSR bits hid a FIFO bug
- the coverage gates and the per-design fault checks
- the comparison between board and harness resources, including the divider
  replica analysis

## Checking the evidence itself

Every claim above is backed by a SHA-256 manifest under evidence/.
`tools/evidence_audit.py` checks those digests against the bytes Git
actually stores, at any revision, and CI runs it on every push:

- `CommitSnapshot` reads blobs through one
  `git cat-file --batch`. A file that exists on disk but was never committed
  counts as missing, which is the failure a working-copy check would miss.
- `claims` turns every manifest layout into claims:
  archive entries, source bindings, and digests recorded without a path.
  `unparsed_digests` fails a manifest holding a digest that no claim
  accounts for.
- `History.digests` gives source bindings every version a path
  had in the audited revision's history, as stored and as a Windows CRLF
  checkout. `History.claim_files_ever` makes a deleted or renamed manifest
  fail.
- `policy` loads the exceptions. Each one is pinned by digest and
  failure status, and must be proven by readable bytes, for example
  `reconstruct` rebuilding a mixed-line-ending working copy, or else
  recorded as a loss.

When it first ran, the audit found 837 claims the committed files did not
back up. Most were simulator files that were never copied into their
archives. The account is in
[evidence-integrity-01](../evidence/2026-10-28/evidence-integrity-01/README.md).

## Questions you should be able to answer

**Why not let the model write the testbench or the contract?** Because then
the model grades itself. Here the testbench is generated from the spec and
golden model, and qualified by mutation. The contract is rendered from
harness-measured facts (`contract_context.py`,
`render_fixed_optimize_contract`).

**How do you know the testbench is any good?** Before grading, it must fail
on a mutated design and on stuck-at outputs (`tbqual.qualification_mutations`). The verifier
audit measured the gap anyway: the generated testbenches caught 18 of 27
injected FIR faults. Better stimulus raised that to 22, and an independent
checker catches all 27.

**What stops a Vivado license hiccup from looking like a bad design?**
`triage.classify` checks infrastructure signatures first (`_INFRA_SIGNATURES`).
Infrastructure outcomes never trigger repair (`_verify_optimization_candidate`)
and are never committed to the journal (`Orchestrator._stage`).

**Could a smaller design that fails timing win?** No. Timing feasibility ranks
above the objective in `select` (`bestofn.py`).

**What happens if the run crashes halfway?** `resume` replays completed stages
from the journal at no cost, verifies their artifact hashes, and retries only
the unfinished or infrastructure-failed work. If the harness code itself
changed, it refuses to continue (`_prepare_inputs`).

**How do you know the archived evidence wasn't edited or lost?** CI audits
every recorded digest against the committed blobs on every push
(`tools/evidence_audit.py`). An archive file that goes missing or changes,
an emptied or deleted manifest, or a stale exception fails the build. When the
audit was introduced it found real holes. Those were fixed by restoring the
exact bytes or proving them another way, not by editing manifests.

**What does it not do?** There is no formal equivalence; verification is
simulation-based. Curriculum tier 0 is held (three consecutive qualifying
campaigns on one frozen harness); the higher tiers are being held next. Board validation is a downstream replay of the winners; the harness
does not yet target board pins itself (see [TARGETS.md](TARGETS.md)). Results
vary between runs: the FIR reached 52 LUTs in one run and 84 in another.
