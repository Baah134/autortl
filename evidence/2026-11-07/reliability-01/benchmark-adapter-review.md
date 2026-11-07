# Minimal VerilogEval adapter review — November 7, 2026

Status: research and interface proposal only. No canonical edit, dataset task
selection, trial, dependency installation, model call, vendor job or board access.
This continues `work/nov6-benchmark-protocol.md`; it does not register or execute
the proposed 40-task, three-arm experiment.

## Upstream pin and grading facts

Read-only GitHub lookup resolves the official `NVlabs/verilog-eval` main branch
to **`c498220d0a52248f8e3fdffe279075215bde2da6`**, committed February 7, 2025.
Use this full commit rather than mutable main. Its recursive Git tree contains
156 `dataset_spec-to-rtl/*_prompt.txt` files, each with a matching `_test.sv` and
`_ref.sv`; the official `problems.txt` also lists156 entries. This is the source
inventory, not a pilot or held-out roster. No task IDs have been selected.
[Commit](https://github.com/NVlabs/verilog-eval/commit/c498220d0a52248f8e3fdffe279075215bde2da6),
[dataset list](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/problems.txt).

The root license is MIT and contains both NVIDIA's project notice and the
bundled OpenAI human-eval notice. Preserve the complete file alongside any
copied grading code or dataset material, plus per-file notices; no license
replacement is proposed. The snapshot has not been downloaded and byte-hashed
by this worker: commit pinning is complete, local artifact registration is not.
[License](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/LICENSE).

The upstream README documents Linux, Python3.11.0 and Icarus Verilog12; it
explicitly excludes development version13. Its complete generation harness also
lists Verilator and LangChain packages. Those generation packages are not
required merely to invoke Icarus on already sealed AutoRTL candidates.
[README](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/README.md).

The pinned Makefile's actual grading recipe compiles candidate, official test
and reference together with `iverilog -Wall -Winfloop -Wno-timescale -g2012 -s tb`,
then executes the compiled result with a30-second timeout. The leading make
error-ignore markers mean a zero make exit is not grading proof. A Python
subprocess wrapper can preserve the compiler flags and timeout without porting
the Bash/make generation workflow to PowerShell. Capture real compiler and
simulator exits independently, with fixed trusted filenames and argument arrays.
Keep compile timeout and simulator timeout distinct; the original recipe's30s
limit is for simulation.
[Makefile](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/Makefile.in).

The official analyzer interprets a zero-mismatch summary as pass only when no
higher-priority recognized compile/runtime error was found. It has several
specific error classes and a generic runtime class; a `TEST PASSED` string is
irrelevant. Its source imports LangChain message classes even though its result
classifier does not use them. Prefer a small licensed, versioned classifier
extraction with differential fixtures against the pinned function, rather than
adding a model framework merely to parse results. Do not import the script
unchanged into the product: its unguarded `main()` executes at import time.
[Analyzer](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/scripts/sv-iv-analyze).

For a reproducible simulator source, official Icarus tag `v12_0` is an annotated
tag object `d61ab44c8a62d10dc80c3ae219387de04b7217c7`, resolving to source commit
**`4fd5291632232fbe1ba49b2c26bb6b2bf1c6c9cf`**. This is a proposed deterministic
v12 baseline, not a claim the paper used that exact build. Before pilots, also
record compiler/build settings, executable hashes and container or OS identity.
No Icarus installation was performed. Earlier read-only PATH discovery found no
`iverilog` or `vvp` on this Windows host; that is not a full-disk installation
inventory.
[Official v12 tag](https://github.com/steveicarus/iverilog/releases/tag/v12_0),
[tag object](https://api.github.com/repos/steveicarus/iverilog/git/tags/d61ab44c8a62d10dc80c3ae219387de04b7217c7).

## Current AutoRTL compatibility

Inspected canonical `run.py`, `autortl/config.py`, `autortl/fsm.py`,
`autortl/tbgen.py`, `autortl/tbqual.py`, `autortl/static_checks.py`,
`autortl/verilog_interface.py` and `llm/client.py` without editing them.

- `build --spec <public intent> --top TopModule` already invokes the planner
  from prose, generates unit oracles/testbenches, verifies modules and produces a
  mechanical wrapper. Omitting `--tb` is essential here: the official test and
  reference are reserved for final grading. `--generate-golden` is only relevant
  when an independent testbench is supplied; its absence is not a mutation
  qualification ablation.
- Single-module generated verification works without a supplied integration
  test. A multi-module design without one ends `build_blocked` after mechanical
  integration; do not feed the official grader in to get around this limitation.
  The pilot must establish a supported single-module route from public intent or
  record this as an actual limitation. Missing support is not permission to
  silently change the benchmark task.
- Build subsequently enters the existing optimization/PPA loop. There is no
  functional-only CLI mode and no supported qualification-ablation switch.
  `done` therefore measures more than external functional correctness.
- The typed schema has specific clock/reset, numeric latency, example and
  supported-interface requirements. Public benchmark descriptions may not state
  an AutoRTL latency or require reset ports. A converter cannot invent those
  ports or learn them from the hidden reference. Preserve the exact public
  module name, directions, widths, signedness, packed ranges and parameters.
- `_qualify_source` runs a positive simulator control before trying bounded
  behavioral mutations. Removing mutation trials alone must retain that positive
  control and all ordinary unit simulation. Skipping the whole function removes
  more than the declared ablation and is not acceptable.
- The existing model client charges attempted backend dispatches and can retry.
  ArmA needs a one-attempt budget, not merely one outer call to `ask`. Retain a
  failed first attempt even if a generic retry path would otherwise run again.
  Router usage records need a per-run sink or an isolated source copy, since
  current recording is repository-local.

## Smallest implementation boundary

Add one experiment entry point, a few pure helpers and focused tests. Reuse the
existing FSM, model client, budget accounting and static gates. No agent roles,
retrieval database, service or scheduling framework is justified.

| Interface | Required input and output |
|---|---|
| `load_manifest(path)` | Validate a frozen protocol/version, upstream commit, allowed task IDs, file hashes, task format, model settings, budgets, environment identity and schedule. Refuse mutable refs, missing hashes and duplicate cells. Pilot/final roster stays unpopulated until the separate selection review. |
| `public_task(task_id)` | Produce only the unchanged public statement plus any reviewed, versioned public-interface annotation applied identically to all arms. Never read a test/reference in the generation process. Record any conversion and its provenance. |
| `run_arm(cell, public_bundle)` | Create a fresh run directory/session with the predeclared budget. A submits one invocation; B/C run the existing loop with a persisted full or mutation-ablation experiment policy. Record all failures and actual tool permissions. |
| `seal_candidate(run)` | Export one deterministic artifact and dependencies, its hash, internal acceptance, exact source selection and termination reason before grading. Never choose candidates using external test results. Missing complete output stays missing. |
| `grade(sealed, private_bundle)` | A separate restricted process verifies hashes, runs pinned Icarus, classifies raw logs, and records real exits, timeout, mismatch count and trusted-test completion evidence. No return path into a generation session. |
| `summarize(cells)` | Reconcile every scheduled cell, including infrastructure/missing outputs; compute the preregistered task-level outcomes and paired uncertainty from machine records. Unknown usage/cost remains null. |

Initially keep the product's complete existing flow and grade its sealed final
candidate separately. A new functional-only execution mode is not required just
to measure external functional success. This avoids weakening production gates
for the study. It may spend effort on FPGA PPA that the functional endpoint does
not reward; publish that cost. If pilots show this makes the intended experiment
unusable, decide on a clearly named, versioned functional-build profile before
final trials. Do not silently replace the full harness with that profile and
retain the same headline.

Candidate export needs a small explicit contract rather than filename guessing:
prefer the accepted incumbent; otherwise the last complete candidate under the
already proposed rule. If a failed build has not emitted a complete top and all
dependencies, report no complete candidate. A mechanical wrapper exporter is
possible but must be deterministic, based only on the public spec, tested and
frozen before trials. Do not repair or alter RTL in the grading process.

For B, persist a narrowly named experiment policy that skips generated-TB
mutation trials only. Include it in saved configuration, runtime identity,
resume validation and every acceptance receipt. The default remains full;
incomplete/unknown policy is rejected. Record B's status as acceptance under the
declared ablation, never as ordinary full-verification acceptance. No global
monkeypatch or unrecorded environment toggle should control this behavior.

## Blockers before any scored run

1. **Hidden-grader access boundary.** A read-only temporary working directory
   does not establish filesystem or network isolation for the current CLI
   worker. Public tests are public on the network as well as on disk. Generation
   needs an enforced restricted environment with only the public bundle and
   approved model/tool channels. Simulator candidates are untrusted executable
   inputs too; grade with no network, bounded resources and minimal mounts.
   Existing command arguments are not proof the operating system enforced this.
2. **Tool/environment qualification.** No pinned Icarus executable or Linux
   grader image is registered. Use an available suitable restricted environment
   if one exists, or obtain/install the needed tooling as a separate reviewed
   step. Xsim compatibility is useful engineering evidence but cannot replace
   the named official Icarus grader in the primary score without a protocol
   amendment and equivalence study.
3. **Prompt representability and export.** Exercise prose-to-contract behavior,
   exact TopModule interfaces, clockless/stateful designs and complete candidate
   export on pilots. Do not import interfaces or behaviors from hidden RTL.
   Predeclare scope restrictions from statements, not observed model failures.
4. **Explicit ablation and attempt accounting.** No recorded policy seam yet
   exists. Positive controls, ordinary simulation and independent grading must
   survive it. Verify the one-dispatch baseline and all rejected-call charges.
5. **Grader semantics and proof.** The official textual classifier alone can
   accept forged or premature summaries. Apply the same existing RTL safety
   boundary to all arms before executing candidates and report blocked inputs
   separately. Retain the official compatibility result alongside stricter
   execution/completion proof. A zero-sample or malformed summary is not strong
   success evidence; qualify the policy against the exact pinned tests rather
   than inventing a universal expected sample count from one example.
6. **Final experiment registration.** Categories/families, pilot and final IDs,
   exclusion table, schedule, model identity and final ceilings still need the
   separate frozen registration. No benchmark score or superiority claim exists.

## Minimum tests before pilots

- Manifest/ref/hash validation, traversal rejection, duplicate cell protection,
  input drift, interrupted append recovery and deterministic candidate sealing.
- Public/private separation using a deliberate sentinel secret and denied file
  and network access, verified from the actual generation process, not just a
  unit-test mock. Test grading logs never re-enter repair context.
- Pure classifier differential fixtures against the pinned upstream function:
  zero/nonzero mismatches, syntax and other compiler errors, timeout, no summary,
  mixed error/zero-mismatch logs and multiple summaries. Preserve upstream class
  plus the stricter process-proof status as separate fields.
- Real grading controls: official reference adapted by a mechanical name change
  only, independently reviewed behavioral faults, syntax failure, infinite loop,
  forged summary and early termination. Require genuine completed positive
  controls and behavioral mismatch negatives. Publish misses and blocked cases.
- B/C policy isolation: default full, B skips mutations only, control failure
  still rejects, ordinary failure still repairs, infrastructure remains separate,
  policy survives resume and changes the cohort identity. Verify real receipts.
- A first-dispatch failure cannot invoke a second backend; missing usage stays
  unknown, and canceled or quota-blocked cells remain in the result denominator.
- Toy/synthetic end-to-end adapter tests run without model, vendor or board
  tools; the later real pilot establishes actual environment compatibility.

The permanent solve here is an explicit experiment boundary with independent
grading and complete accounting. Selecting favorable tasks or treating the
existing curriculum hold as a public benchmark would not establish the desired
CV result.
