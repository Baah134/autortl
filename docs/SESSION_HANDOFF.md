# Current AutoRTL checkpoint

Updated October 23, 2026 (America/New_York). Recover from Git, ownership,
source hashes and raw results; chat summaries are supplementary.

## Checkout and published history

- Canonical: C:/Users/prince.baah/Downloads/autortl-work. Preserve Downloads/autortl.
- Branch: codex/contract-context. Last verified main/dev:044a3d5.
- Packet01 completed:23LUT/31FF,setup+.078ns/hold+.106ns, timing recovery
  from invalid15LUT/6FF,-.946ns. Exact saved winner independently passed;
  actual DONE331identities/budget/fileset unchanged. Archive421files.
- Fresh fulltier0 campaign08 passed2/2,streak2,heldfalse; cohort9b69c8d0.
  Counter55->53LUT; mux8LUT baseline retained. Earlier counter31LUT result
  remains separately archived. No held tier or controlled weak-model claim.
- Runtime55-file implementation unchanged from85e4fb8; current stage only
  adds a fixture, qualification adapter/tests and documentation/evidence.

## Active engineering: multi-cycle unsigned divider

Fixture:curriculum/tier3/iterative_divider_build. Child WIDTH1..16, default8
wrapper; selected widths8wrapper+children1,2,4,13,16. Atomic unsigned q/r,
single outstanding request, ready=!busy&&!out_valid. Captureedgek, WIDTH
computeedgesk+1..k+WIDTH, firstvalidpostNBAk+WIDTH, earliestretireWIDTH+1.
Scalar latency9 is default8 only. Div0Qallones/Roriginal, same schedule.
Syncreset aborts computation/heldresult; no acceptance on retirementedge.
Preferred restoring arithmetic; simulation alone cannot prove physical structure.
Supervised reference is qualification-only, NEVER a generator seed.

Admission01 failed20/21: reset_preserves_held_result passed because ready1
allowed normal retirement to hide ignored reset. Original212-file evidence
preserved BEFORE correction at evidence/2026-10-22/divider-admission-attempt-01.
Only TB and its tests changed: added held-result/ready0 reset and distinct
mandatory reset_stalled_result counter. Reference/spec/all20faults unchanged.

Admission02 now PASSED21/21: control sixwidths and20actualbehavioralassertions,
no compile/infra/watchdog kills. Fullsuite1180passed429.28s; focus107passed7.81s.
All192 frozen identities matched at recovery and archiving. Source manifest:
workspace/work/divider-source-freeze-02.json. Successful archive199files:
evidence/2026-10-23/divider-admission-attempt-02. README-only publication update
must be recorded as a documentation delta, not claimed byte-identical.

## Ownership / jobs

Previous lease expired. Reclaimed October23 after confirming no owned jobs;
new coordinator:Codex coordinator / 2026-10-23 divider validation,8hlease.
Token retained privately. Claims in SQLite:
divider-contract/Codex/divider-contract (spec/meta/README/reference),
divider-tb/Codex/divider-tb (TB),divider-qualification/Codex/divider-qualification
(cases/tests),divider-driver/Codex/main (adapter/tests),divider-notes-23 and
divider-evidence-23/Codex/main. Worker executable files remain frozen.
Old qualification56557/fullsuite44361 are complete, no owned tools running.
Old awakehelper13973 is no longer running; restart bounded helper for new queue.
User Vivado GUI remains untouched. One vendor implementation job at a time.

## Exact next action and immutable experiment budget

Review/archive/commit/push admitted fixture, then launch NEW
logs/build-golden-divider-01 (never resume an old spent experiment):

```powershell
python -u run.py build --spec curriculum/tier3/iterative_divider_build/design_spec.json --tb curriculum/tier3/iterative_divider_build/iterative_divider_tb.v --top iterative_divider --generate-golden --objective minimize_luts --iterations 3 --best-of-n 1 --max-llm-calls 16 --max-vivado-minutes 25 --max-wall-minutes 35 --max-infra-retries 1 --vivado C:/AMDDesignTools/2025.2/Vivado/bin/vivado.bat --xvlog C:/AMDDesignTools/2025.2/Vivado/bin/xvlog.bat --xelab C:/AMDDesignTools/2025.2/Vivado/bin/xelab.bat --xsim C:/AMDDesignTools/2025.2/Vivado/bin/xsim.bat --output-dir logs/build-golden-divider-01
```

Record launch commit/runtime hashes, freeze source during run. After completion:
independent exactsavedwinner/children check, actualDONE integrity, supplemental
generated-grader sensitivity if useful (workspace/work/measure_divider_grader.py;
excludes three width-only faults inapplicable at default8), then freshfulltier0
before main integration. Preserve all failed outcomes. No generated divider/PPA
result is claimed before actual tools. Proposal-feedback study remains in
TASKS; user prioritizes advancing complex designs now. No new role/framework.

Python:C:/Users/prince.baah/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
PYTHONPATH:C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work/review_deps
Set PYTHONDONTWRITEBYTECODE=1; fresh pytest basetemp and no cacheprovider.
Downloads writes/Git/vendor tools require authorized escalation.
