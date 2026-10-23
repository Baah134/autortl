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

## Completed generated divider01 / active harness correction

Launchcfef8af, modeljob66886 finished0. DONE bestiter3:26LUT/38FF,
setup+.315ns/hold+.129ns,31.58%LUTreduction from38LUT/46FF,+.324/.136ns.
Estimatedpower .092->.103W increased.11calls,409.939chargedtoolseconds,
560.999elapsedseconds,original3iterations/1candidate/16calls/25tool/35wallmin.
Oracledivmod rejected/repaired; dualinitialgraders caughtflip==to!=. Iter2
duplicated/rejected,iter3sharedsubtractwon. Actualsourceis8steprestoring.
Exact savedwinner/declaredchild independentcheckPASS. ActualDONE251identities,
fileset/budget unchanged; child/spec tamperrejected,restored. No in-flightkill
proof. CRLF/LF normalizedcompletecodeequal,independentcopybytesame.
Archive:evidence/2026-10-23/generated-divider-attempt-01 (436filesverified).

Generatedgradermeasurement94764 finished0: passingcontrol,13/17applicable
faults detected; missedzero_divisor_remainder_zero,ready_on_retirement_edge,
asynchronous_reset,reset_preserves_held_result. Width-only3faultsexcludedat8.
Spec hasaccepted255/0=>R255, butactualRTLstimulusonlytested0/0. This is the
observed next harness correction; original01MUSTNOTberesumed/regradedunder
changedruntime. Rawresults/sourceidentitiesalreadyarchivedbeforechange.

## Current tested coverage correction / merge gate

Worker completed autortl/tbgen.py +tests/test_tbgen_examples.py; read-only review
found no blocker. Parentfocus140passed2.35s; fullsuite1226passed175.87s.
All193identities inworkspace/work/scoreboard-example-source-freeze-01.json
matchthroughvalidation/archive. Actualcontrolledexperiment6026 completed0:
oldcontrolPASS/oldzeroRmutantPASS, newcontrolPASS/newzeroRactualassertion.
Newgrader14/17vs13/17; readiness/reset3missesretained.103->108vectors;
3corners andexact100randomtail unchanged. No modelcalls ororiginalFSMresume.
Originalrun250experiment-protectedhashes/state/budgetunchanged, notthe same
setas251actualDONEscope; bothproofsretained. Coveragearchive174files:
evidence/2026-10-23/scoreboard-example-coverage. Initialprelaunchhelperfailure
retained separately; qualifiedoracle boundtoreceipt+publishedarchivehash.

Fullsuite7477finished0. No actualvendor/modeljobactive atthischeckpoint.
Awakehelper55214 remainsbounded120min; releaseafterqueue. Source frozen.
Next: commit/push testedcoveragefix, launch freshfulltier0campaign09:
1iteration/1candidate,16calls,20tool/30wallminutes,1infraretry perentry,
sameVivado/device/100MHz/idealzeroI/O. Runtimechanged(tbgen), oldstreak2 MUST
NOTcarryover. No higherheldtier. Afteractualpass archive/sourceverify then
authorizedatomicmain/devintegration. Currentmain044a3d5; devb20b5b4 before
newcommit. Actualheads verifiedafterpush. Do notresume originaldivider01
undernewruntime; its PPA remains tiedtocfef8af andimmutableevidence.

Python:C:/Users/prince.baah/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
PYTHONPATH:C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work/review_deps
Set PYTHONDONTWRITEBYTECODE=1; fresh pytest basetemp and no cacheprovider.
Downloads writes/Git/vendor tools require authorized escalation.
