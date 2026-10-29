# How AutoRTL works: a guided tour of the code

This tour follows one `optimize` run from the command line to a verified
winner, then covers build mode, crash-safe resume and the hardware suite. Each
step points to the code that does it, as `file:line`, so you can open it and
read it. It also answers the questions people ask most about the design.
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
| CLI | `run.py` | `optimize`, `build`, `resume`, `bench` subcommands (`run.py:49`, `:54`, `:62`, `:65`) |
| Orchestrator | `autortl/fsm.py` | The run loop, stage journal and verification ladder (`class Orchestrator`, `fsm.py:143`) |
| Contract | `autortl/contract_context.py` | Renders the fixed, hash-bound optimization contract (`:265`) |
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
(`fsm.py:229`) does two things:

- It hashes every harness source file into `runtime.json`.
- It copies the design, testbench and spec into the run folder with their
  hashes.

On resume, a changed harness file or input aborts the run, so a result can
never be silently regraded by different code (`fsm.py:241`, `fsm.py:260`).

**2. Verify the baseline.** Optimization is refused without a testbench
(`fsm.py:690`). The original design goes through the full flow: compile,
simulate, synthesize, place and route (`fsm.py:702`). Then two gates check the
result:

- The metrics gate (`fsm.py:717`) rejects impossible numbers. A LUT total of
  zero or a missing WNS raises `MetricsGateError` (`metrics_gate.py:15`).
- Tool exit receipts must also pass (`fsm.py:720`).

**3. Freeze the contract.** The harness collects facts it measured itself:

- source and testbench SHA-256
- part and clock period
- baseline metrics and declared latency
- constraints and report hashes

It renders them into a contract (`fsm.py:729-744`,
`contract_context.py:265`). The model sees this contract but cannot edit it.
If the contract on disk ever differs from the re-rendered one, the run stops
(`fsm.py:739`).

**4. Plan.** When needed, the planner role writes a plan
(`fsm.py:797-808`). It is bound to the hash of the exact design it was
written for, and a plan for a different seed stops the iteration
(`fsm.py:809`).

**5. Generate best-of-N candidates.** Each candidate comes from a different
mutation prompt for the objective (`bestofn.py:46`). `dedupe` drops
byte-identical sources (`bestofn.py:51`), so the same design is never paid for
twice.

**6. Climb the verification ladder** (`_verify_optimization_candidate`,
`fsm.py:1147`). Each rung is cheaper than the next, so most bad candidates die
in milliseconds:

1. Static check of ports, widths and signedness (`fsm.py:1163`). Then *spec is
   law*: a declared `@latency` that differs from the contract is a failure,
   not a negotiation (`fsm.py:1169-1172`).
2. `xvlog` compile (`fsm.py:1179`).
3. Simulation against the qualified testbench (`fsm.py:1185`).

A design failure gets a bounded number of repair attempts. Each repair prompt
carries the taxonomy's hint for the Vivado message IDs found
(`fsm.py:1198`). Every repaired answer re-enters the ladder from rung 1. An
infrastructure failure leaves the candidate *unverified*: it never triggers a
repair and never changes the RTL (`fsm.py:1190`).

**7. Synthesize survivors** (`fsm.py:833-874`). A cached result is reused only
if it is still for the same source, testbench and tool context, and if it
passes the metrics gate again (`fsm.py:836-852`).

**8. Select deterministically** (`bestofn.py:64`). Candidates are sorted by:

1. rungs passed
2. timing feasibility
3. the objective metric
4. source length

So a design that meets timing always beats a smaller one that doesn't.

**9. Repeat** until the iteration count or the budget runs out. As the budget
shrinks, best-of-N degrades from N to 2 to 1, and replanning stops below 30%
remaining (`budget.py:70-80`). The budget can only be charged, never refunded
(`budget.py:41-51`).

## The invariants, and where each is enforced

| Invariant | Where |
|---|---|
| Spec is law (interface, latency) | `fsm.py:1163-1172`; contract re-render check `fsm.py:739` |
| Model text never reaches TCL or a shell | Paths are sanitized for TCL (`vivado.py:24`); TCL comes only from templates (`vivado.py:1-5`); the model runs in a read-only sandbox (`codex_cli.py:187`) |
| Severities are promoted, never demoted | `promotion_tcl` emits only `-new_severity ERROR` (`vivado.py:163-170`) |
| Infrastructure failures never mutate the design or count as attempts | Classifier `triage.py:39`; ladder `fsm.py:1190`; journal keeps infrastructure outcomes uncommitted so a resume retries them (`fsm.py:346-348`) |
| A testbench must catch bugs before it grades | `tbqual.py:53` builds an operator mutant plus stuck-at-0 and stuck-at-1 stubs; `_qualify_source` (`fsm.py:434`) requires a retained assertion failure |
| Metrics must be plausible | `metrics_gate.py:15` |
| Results cannot be silently regraded | Runtime and input freezing, `fsm.py:229-275` |
| A testbench never grades a stale child | A candidate that stops instantiating a companion the trusted testbench tests directly is rejected before any tool runs (`fsm.py:1174`, `companions.py:77`) |
| A locked checkpoint is infrastructure, not a crash | `CheckpointLockedError` (`state.py:24`) keeps the old checkpoint intact; `run.py` reports `infra_blocked` and the run resumes |

## How the testbenches work

`tbgen.generate` (`tbgen.py:283`) picks one of two compare modes from the
spec:

- **Fixed latency** (`tbgen.py:203`): it drives one stimulus per cycle and
  compares each output `latency` cycles later.
- **Scoreboard** (`tbgen.py:222`), for valid/ready designs. It:
  - applies periodic backpressure on `out_ready` (`:240`)
  - inserts input bubbles that carry changing invalid data (`:244-248`)
  - holds the producer stable while blocked
  - adds off-edge reset pulses for synchronous-reset contracts (`:250-256`)
  - checks that `out_valid` never drops and the output stays stable while
    stalled (`:261-263`)
  - checks that no result appears before the minimum transfer latency
    (`:270-271`)
  - checks that the scoreboard drains exactly (`:277-278`)

Expected values come from the Python golden model under the same reset
initialization as the RTL driver (`tbgen.py:128`).

## Build mode

`_run_build` (`fsm.py:493`) turns a typed spec into a design:

1. Lint the spec (`fsm.py:508`).
2. Elaborate stub modules, so a broken blueprint fails before any generation
   (`fsm.py:515-519`).
3. Generate and verify each module in turn against its own qualified
   testbench (`fsm.py:521`).
4. Write the top level mechanically, with no model involved
   (`linter.top_verilog`, `fsm.py:540`).

The result then becomes the baseline for optimize mode.

## Crash-safe resume: the stage journal

Every model call, tool run and decision goes through `_stage`
(`fsm.py:305`):

- Each stage gets a deterministic identity: scope, category, name and an
  occurrence index.
- A completed stage saves its result and its artifact hashes
  (`fsm.py:349-360`).
- On replay, a completed stage returns its saved result instead of running
  again, and its artifacts must still match their hashes (`fsm.py:314-324`).
  This is why `resume` costs no extra model calls for finished work.
- Infrastructure failures are deliberately not committed, so the next resume
  retries them (`fsm.py:346-348`).

The tool wrapper `_tool` (`fsm.py:386`) does two more things:

- It charges tool time to the budget and caps each timeout at the time
  remaining.
- For simulation, it records the exact verified inputs and refuses a replay
  if they changed (`fsm.py:413-426`).

## The model call

`codex_cli.py:187` runs `codex exec --sandbox read-only --ephemeral --json` in
a fresh temporary directory, with the prompt on stdin. A timeout kills the
worker's whole process tree; on Windows that is `taskkill /T /F`
(`codex_cli.py:100-104`). No API key is involved; it uses your existing Codex
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

- `CommitSnapshot` (`evidence_audit.py:110`) reads blobs through one
  `git cat-file --batch`. A file that exists on disk but was never committed
  counts as missing, which is the failure a working-copy check would miss.
- `claims` (`evidence_audit.py:281`) turns every manifest layout into claims:
  archive entries, source bindings, and digests recorded without a path.
  `unparsed_digests` (`:269`) fails a manifest holding a digest that no claim
  accounts for.
- `History.digests` (`:194`) gives source bindings every version a path
  had in the audited revision's history, as stored and as a Windows CRLF
  checkout. `claim_files_ever` (`:208`) makes a deleted or renamed manifest
  fail.
- `policy` (`:368`) loads the exceptions. Each one is pinned by digest and
  failure status, and must be proven by readable bytes, for example
  `reconstruct` (`:421`) rebuilding a mixed-line-ending working copy, or else
  recorded as a loss.

When it first ran, the audit found 837 claims the committed files did not
back up. Most were simulator files that were never copied into their
archives. The account is in
[evidence-integrity-01](../evidence/2026-10-28/evidence-integrity-01/README.md).

## Questions you should be able to answer

**Why not let the model write the testbench or the contract?** Because then
the model grades itself. Here the testbench is generated from the spec and
golden model, and qualified by mutation. The contract is rendered from
harness-measured facts (`contract_context.py:265`).

**How do you know the testbench is any good?** Before grading, it must fail
on a mutated design and on stuck-at outputs (`tbqual.py:53`). The verifier
audit measured the gap anyway: the generated testbenches caught 18 of 27
injected FIR faults. Better stimulus raised that to 22, and an independent
checker catches all 27.

**What stops a Vivado license hiccup from looking like a bad design?**
`triage.classify` checks infrastructure signatures first (`triage.py:17-28`).
Infrastructure outcomes never trigger repair (`fsm.py:1190`) and are never
committed to the journal (`fsm.py:346`).

**Could a smaller design that fails timing win?** No. Timing feasibility ranks
above the objective in `select` (`bestofn.py:81-84`).

**What happens if the run crashes halfway?** `resume` replays completed stages
from the journal at no cost, verifies their artifact hashes, and retries only
the unfinished or infrastructure-failed work. If the harness code itself
changed, it refuses to continue (`fsm.py:241`).

**How do you know the archived evidence wasn't edited or lost?** CI audits
every recorded digest against the committed blobs on every push
(`tools/evidence_audit.py`). An archive file that goes missing or changes,
an emptied or deleted manifest, or a stale exception fails the build. When the
audit was introduced it found real holes. Those were fixed by restoring the
exact bytes or proving them another way, not by editing manifests.

**What does it not do?** There is no formal equivalence; verification is
simulation-based. There is no held curriculum tier yet, and the designs are
small. Board validation is a downstream replay of the winners; the harness
does not yet target board pins itself (see [TARGETS.md](TARGETS.md)). Results
vary between runs: the FIR reached 52 LUTs in one run and 84 in another.
