# Durable task board

Inspect Git and the local coordination status before claiming work. A task
marked in progress may contain saved changes from an interrupted coordinator.
Do not overwrite them. Live claims use scripts/session.py; this board travels
with Git and states acceptance criteria.

| Task | Status | Completion evidence / remaining acceptance |
|---|---|---|
| Codex runtime and generated counter | Published | Commit 68fc5e6; 226 tests at checkpoint; generated 8-bit counter passed simulation, mutation checks and routing |
| Relocate canonical clone | Complete | Downloads/autortl-work; 317 source/Git file hashes matched before and after move |
| Provider-neutral shared memory | Published | 8d5eb09; lease/task/handoff CLI; concurrency/ownership and full-suite tests; checkpoint retains active coordinator |
| Atomic config/state/budget/cache | Tested | Strict persistence, cache provenance and integrated FSM recovery tests pass |
| Generated TB timing and handshake | Implemented, tested live | All 9 Vivado cases behaved as expected; retain logs and hashes |
| Restricted golden execution | Tested | Child process, AST restrictions and resource limits tested; remaining allocation limits documented in RECOVERY.md |
| Exact Verilog interfaces/static checks | Implemented | 23 focused tests pass; parameterized counter and grouped mux covered |
| Recoverable optimize/build FSM | Tested with controlled tools | Interruption, DONE replay, config/report/source drift, budgets, infra retries and build integration tests pass; live campaign next |
| Curriculum governance and fixtures | Tested | Three matching full cohorts and mandatory gates covered; no newly held tier claimed |
| First live counter/mux campaign | Recorded: 0/2 | Counter baseline 54 LUTs/37 FFs, WNS 5.491 ns; model budget/timescale failure; mux boundary timing missing; no tier held |
| Live regression repairs | Integrated into main | 387fe0e; 423 tests pass; counter replay passes; mux simulation/routing passes: 8 LUTs/8 FFs, WNS 0.579 ns, WHS 0.052 ns; all failed attempts retained |
| Authoritative context and counter reference | Published 4091a4b | 436 tests, five real counter cases; stronger context preserves source/constraints and evaluation facts |
| Fresh model-driven tier0 campaign | Recorded 0/2, recovered DONE | Worker exits preserved; counter physical 55->53 LUT candidate rejected due missing report context; no accepted gain/tier |
| Harness feature audit | Active | docs/HARNESS_REVIEW.md: keep verification/journals, improve evidence/provider boundaries, constrain legal transformations, remove dead controls |
| Provider/report/legal transformation repairs | Implemented; validating | Typed resumable model blocks, bounded diagnostics, timing manifest, hold diagnosis and physical command, unsupported parallel control rejected |
| Deterministic contracts and actual prompt conformance | Implemented; validating | Campaign02 reproduced six wasted negotiation calls; fixed contract preserves gates; all roles receive conventions and consistent references |
| FIFO reference qualification | Live checked:6/6verdicts | Full comparator cycle repaired; AW2/AW4 controls pass and data/full mutants assert; no physicalCDC proof |
| Build counter8 and priority encoder | Completed and archived | Counter6LUT/8FF; accepted encoder6to5LUT/4FF; generated verification plus independent final tests pass |

The active coordinator continues with bounded live campaigns after publication.
Do not treat the previously verified standalone generation trial or controlled
unit tests as proof of the complete live build/resume/optimization loop.


Latest interface/storage checkpoint: 554 regression tests pass; real Windows
sharing-lock recovery and four signed/symbolic Vivado cases pass expected
verdicts. Original campaign03 remains1/2. Structural declaration safeguards
supplement independent verification; they do not establish full equivalence.

## Current evidence boundary (2026-10-20)

Published2318e42:554fullregressiontests,24actual simulation verdict checks,
Windows sharing-lock recovery and structural interface safeguards. Earlier
focused counts are historical. Campaign04 completed2/2 under historical
governance with baselines retained; no accepted gain/held tier. Fixed contracts,
role conventions and provider diagnostics are published and live exercised.

Active milestone: actual exit receipts and deterministic gates; cache/DONE
raw-log integrity; source/TB/companion-bound Doctor reuse; unknown source
latency; explicit UTF8 guidance; runtime-bound curriculum streaks. Run full
tests and a fresh frozen campaign before integration.

### Next live build coverage

Run serial fresh builds for counter8_build/design_spec.json (top counter8) and
encoder8_build/design_spec.json (top priority_encoder8), deliberately without
--tb to exercise golden generation, example qualification and generated module
TBs. Use one iteration/candidate,16calls,20toolminutes,30wallminutes,oneinfra
retry and the same explicit Vivado binaries. Supplying the independent top TB
currently takes the trusted-test branch and bypasses golden generation.

Afterward independently simulate only the saved <top>_best.v plus its child
modules/<top>_core/<top>_core.v against the corresponding checked-in <top>_tb.v
in a fresh output directory. Do not recursively glob RTL (duplicate tops,
stubs and TBs). Generated child-derived top verification is not independent.

Counter trusted TB covers700cycles, wrap/hold/midrun reset; encoder covers all
256patterns ascending/descending plus valid and edge behavior. Generated default
counter stimulus is too short for8bitwrap and has only initial reset; sparse
IOexamples do not establish oracle correctness. Qualify the independent top TBs
with behavior-specific overflow/hold/reset and priority/valid/latency mutants
before interpreting success as broad build coverage.

Current receipt/latency/runtime-identity milestone: **655tests passed**. Source
is frozen for fresh campaign05; initialfixturefailures are preserved separately.

## Fresh05 completed

**655tests; fulltier0 2/2; one accepted55to53LUT counter gain.** Actual DONE
replay is checked. Receipt/input integrity, unknown latency, UTF8 decoding and
runtime-bound governance are implemented and live exercised where applicable.
No heldtier/weak-model claim. Typed golden/build, independent top verification,
cache/restart ablations and in-flight recovery remain the next coverage work.


## Streaming progression

- Two-entry8bit elastic ready/valid buffer fixture: schema/static/unit16tests pass;
  independent queue TB plus reference/eight faults prepared. Runtime runner adds
  --suite skid; focused26tests pass, no hardware verdict implied by those tests.
- Admission: real reference pass and all8faults assert; generated golden/build
  path without--tb; independent final saved-winner+child check; real routed metrics.
- Final verification runner copies only the declared winner/children and the
  independent supplied TB, with byte hashes; never recursively glob buildRTL.
- Before main integration: finalfullsuite and freshfulltier0 under frozen runtime.
  Higher-tier design completion does not by itself establish a held tier.


## Current completed progression and integration gate

Counter8 and priority encoder generated builds are complete and independently
verified. Combined generated+independent streaming build03 is complete atafcc080:
15LUT/19FF, positive setup/hold; baseline retained. Its saved winner and child pass
the independent queue TB; DONE replay preserves42selected identities. Earlier
attempt failures remain separate. No weaker-model or held-tier claim.

Final proof-retention and duplicate-definition repairs have focused tests and a
real compiler regression. Fullsuite07 is active; next publish tested source,
run freshfulltier0 campaign06, archive the exact cohort and integrate main only
on passing gates. Next design complexity: parameterized synchronous FIFO with
pointer wrap, capacity and sustained throughput verification, before packet or
multi-clock pipelines. Research/feature decisions remain harness-first.
