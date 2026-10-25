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

Final proof-retention and duplicate-definition repairs passed807fulltests and a
real compiler regression. Source8098466 freshfulltier0 campaign06 passed2/2,
including accepted55to31LUT counter gain; exact cohort was archived and integrated
into main ata113ca1. Next design complexity: parameterized synchronous FIFO with
pointer wrap, capacity and sustained throughput verification, before packet or
multi-clock pipelines. Research/feature decisions remain harness-first.


### Next design acceptance plan: parameterized synchronous FIFO

Add a standalone tier2/sync_fifo_build experiment after the current integration
checkpoint. Reuse the two-entry buffer's independent shift-queue checker and
qualification runner conventions; the asynchronous FIFO is a different CDC task.
No new runtime mechanism is currently required.

- Child sync_fifo_core defaults WIDTH=8, DEPTH=3. Supported experiment domain:
  positive WIDTH1..16 and DEPTH1..8; this bound is not universal parameter proof.
- Ports: clk, rst, in_data, in_valid, in_ready, out_data, out_valid, out_ready.
  Synchronous active-high reset flushes occupancy. No empty bypass, minimum
  transfer age1. out_valid=count>0; in_ready=(count<DEPTH)||out_ready.
  Full simultaneous pop/push is permitted; stalled valid/payload remain stable;
  invalid output data is unspecified. Avoid adding a conflicting ready-isolation
  claim. The depth-three default must wrap explicitly instead of truncating bits.
- The current generated wrapper binds child defaults and does not expose public
  top parameters. The trusted TB should test the default wrapper and explicit
  child instances at(1,1),(8,2),(8,4),(13,5),(16,8), compiling the same child source once.
  Measure PPA only for the default8x3 top; extra matrix instances are TB-only.
- Generated golden oracle remains transaction payload identity. Combine it with
  the independent temporal TB using --generate-golden and --tb. All instances
  must finish, with per-instance assertions and a bounded global watchdog.
- Before model generation, qualify reference behavior and faults for hardcoded
  width/depth defaults, power-of-two-only wrap, early/late full, lost simultaneous
  transfers, truncation at width13, empty bypass, stall instability and async
  reset. Compilation/watchdog/infra failures do not count as detected RTL bugs.
- Test schema/static/default parameter bindings and oracle/matrix manifests;
  retain every real mutation outcome, input identity and raw assertion. Only
  begin model build after admission passes. Do not edit runtime during a frozen
  campaign or claim full-tier promotion from this one design.

Implementation now exists in curriculum/tier2/sync_fifo_build with six matrix
checkers and13faults. Focused26fixturetests and29runnertests pass. Real admission
passed14/14expected verdicts and fullsuite836tests passed. Generated default
payload control passed too. Next: model-driven combined build, with no generated
FIFO physical result claimed until actual routing and independent checks.


### Active FIFO recovery gate (2026-10-21)

FIFO01 at ffc15fc passed functional checks but failed setup (-0.931 ns).
Preserve its failed attempt. Current recovery changes are feasibility-first
policy, frozen-companion guidance, bounded compile/sim repair, UTF-8 IO and DONE
child-source identities. Final fullsuite and fresh fulltier0 are required before
main integration. Run FIFO02 on a newly committed frozen runtime; independently
check the exact saved winner and declared child, then test completed-run reuse.

After timing closure: packet-tagged FIFO, adding only in_last/out_last to the
same ready/valid contract. Keep data/last atomic and stable while stalled.
Cut-through beat delivery is permitted; reset aborts queued/partial packets.
Qualify sideband stuck/current-input/misalignment/stall/reset faults, plus FIFO
capacity/order faults. Test lengths1,2,3,4,7,17, depth crossings, consecutive
single-beat packets, stalled endings and full simultaneous boundary transfers.
No packet parser, CRC, store-and-forward, CDC or new harness role is required.

## Active continuation 2026-10-21: annotation authority

FIFO04 on d39e34d finished with baseline retained. Candidate2 passed behavior
and routed setup/hold (24LUT/27FF,.318/.050ns), but reviewer invented a required
numeric top annotation despite known=false. Preserve original failure archive04.

1. Complete isolated wrapper/prompt/convention correction and review; runtime
   frozen during focused/full regression tests. No weakening of typed contracts.
2. Publish tested milestone. Fresh FIFO05 predeclared:3iterations/1candidate,
   16calls,25tool/35wallminutes,oneinfraretry. Original04 is never regraded.
3. Independently simulate exact final saved top and declared children; validate
   actual DONE replay/input tamper behavior before any further runtime edits.
4. Fresh complete tier0 campaign07,1iteration/1candidate,16calls,20tool/
   30wallminutes,oneinfraretry, same target/constraints/toolchain.
5. Archive actual outcomes, update public verified results and feature review,
   then integrate main only if complete regression/fulltier0 gates pass.
6. Next complexity after an accepted FIFO closure: packet-tag bit FIFO, checking
   tuple order/stability through stalls, full simultaneous transfer, wrap/reset.
   Reuse ladder and dual graders; no new framework/roles.

### Next complexity proposal: packet-tagged FIFO

After acceptedFIFO05 closure and fulltier0 gate, add packet_fifo_build with
WIDTH8/DEPTH3 defaults and the same six parameter checks. Add only in_last/
out_last as ordinary payload ports (protocol=none). Each accepted tuple
(data,last) remains ordered/stable through stalls; reset flushes all queuedbeats,
including partialpackets. Invalid data/last unspecified; last is a marker,
not store-and-forward control. Reuse current multi-output golden/scoreboard
support; no new role, queue framework, CRC, parser, arbitration orCDC.

Independent directed lengths1,2,3,4,7,17; identical data/different markers,
singlebeat packets, marker endings under stall, full simultaneous transfers
across boundaries, nonpoweroftwo wrap, occupied/reset/partialpacket flush and
idleinput marker changes whileoutputstalled. Retain preedge/postNBAchecks,
watchdog/allcasecompletion and percase beat/marker accepted-retired-discarded
accounting; no marker required on an aborted partial packet.

Proposed admission:1control+19faults (current13adapted, plus laststuck0,
laststuck1, currentinputlastbypass, unacceptedtagwrite, displacedtagread,
tagonlystalldrift). Require actual behavioral assertion for each, retain exact
mutations/hashes and misses. Generated qualification currently stops after a
detected global mutant; this is not sideband-specific sensitivity. Measure
both graders on named sideband faults before changing runtime qualification.
This is a reviewed proposal, not new tested/physical evidence.

Packet fixture admission completed October22:1105fulltests,60focusedtests,
20/20realexpectedverdicts. Allsixcontrolconfigurationspassed;19namedmutations
caughtactualassertions. No runtimeextensionrequired. Freshpacket01 nowadmitted
withoriginal3iteration/16call/25tool/35wallminute budget. Remaining: generated
gradernamedsidebandmeasurement, modelphysicaloutcome,exactwinner/DONE checks,
freshfulltier0 andmainintegration. No generated/PPA result claimed inadvance.

Packet01 completed:23LUT/31FF,+.078/.106ns timing recovery; independent saved
winner and331-identity DONE checks passed. Generated grader caught6/6named
marker faults, still missed readinessflip. Archive421files. Fresh fulltier0
campaign08 active14413; main integration pending. Next harness study should
target repeated proposals after churn/replan under an equal original budget,
using retained packet01 as failure evidence; no new mechanism is yet approved
by evidence. Plan and compare simpler feedback before implementation.

### Reviewed next harness study: previous proposal feedback

Observed packet01 repeated exact standard RTL across three iterations, including
a scheduled/stall replan. CHURN is visible to planning but is not a direct
need_plan condition; adding it alone would not solve this reproduced case.
Generation lacks a compact prior instruction/source/outcome record.

Plan bounded, journaled feedback for planner/generator: prior instruction, source
identity, equality to current seed, measured standard-flow outcome, separately
identified Doctor outcomes. Request a concrete change from an already tried
proposal. Preserve cache, immutable contracts, original budgets and acceptance.
Do not automatically reject repeated RTL: changed physical settings produced
the accepted packet winner. No extra role or population framework.

Before implementation, define deterministic mocks for feedback identities,
standard-vs-Doctor separation, incumbent retention and identical replay without
extra calls. Then full regression and fresh fulltier0 gates. Evaluate three
matched baseline/feedback pairs with same observed-model configuration, task,
constraints, N=1 and original budget; report duplicate generation, distinct
verified candidates, calls/tokens, tool time, completion and accepted improvement.
Retain only if repetition decreases without reduced verified completion or
material added cost. A new source hash alone is not success. Research basis:
docs/RESEARCH.md precision-feedback decision and existing primary sources.

Packet milestone final gates passed:1105fulltests,freshfulltier0campaign08
2/2(streak2,heldfalse),exactwinnerindependentcheck,DONE331identities. Archive
counts202admission/421packet/195campaign verified. Readyforauthorizedmainmerge.
Next executable engineering stage is the reviewed previous-proposal feedback
study above; inspect actual Git/ownership first, then claim exact scopes.

## User steering: advance to multi-cycle arithmetic (October22)

Counter is complete; tier0 counter/mux runs are regression gates, not the next
design objective. Packet01 is complete and merged. User requests more complex
designs now. Next experiment: iterative_divider_build (unsigned quotient and
remainder), reusing one valid/ready input and output channel plus multi-output
scoreboard. Proposal-feedback study remains recorded for an observed need;
advance arithmetic first, without adding a runtime mechanism preemptively.

Plan before implementation: child iterative_divider_core #(WIDTH=8), fixed
default top iterative_divider. Supported WIDTH1..16; selected defaultwrapper8
and explicit children1,2,4,13,16. Capture unsigned dividend/divisor only on
in_valid&&in_ready. Single outstanding transaction, no input acceptance while
computing or holding a result: in_ready=!busy&&!out_valid. At acceptance edge k
capture operands; execute WIDTH bounded arithmetic iterations on edges k+1
through k+WIDTH. out_valid first becomes visible after edge k+WIDTH and earliest
retirement is edge k+WIDTH+1, so minimum accepted-transfer age WIDTH+1 (default9).
No early result for trivial operands/dividebyzero. Quotient=floor(a/b),
remainder=a%b for b!=0; b==0 returns allones quotient and original dividend
remainder. Hold valid/quotient/remainder during output stall. Synchronous
activehigh reset aborts computation and queuedresult, dominates transfers;
invalid output fields unspecified. Consecutive requests are allowed with the
explicit busy/result boundary; no sameedge inputacceptance on resultretirement.

Golden oracle maps accepted inputs to eventual quotient/remainder; temporal
TB independently checks availability exactly, legal held producer, no duplicate
or lost results, reset at each computation phase, dividebyzero timing, busy and
result stalls, operand noise after capture, conservation and allcasecompletion.
Exhaustively test smallwidth inputs, directed highbit/exactdivision/max operands
and deterministic randomized largewidth cases. Reference qualification only,
never generator seed. Qualify arithmetic/width/capture/latency/stall/reset/readiness
mutations with actual assertions before model generation. Compile/infra/watchdog
are not kills. Freeze source for full regression and retain exact inputs/verdicts.
No new engine/role unless the fixture exposes an actual unsupported requirement.

Divider model experiment predeclared after admission: fresh logs/build-golden-divider-01, typed spec plus independentTB and --generate-golden; no supervisedreference seed.3iterations/1candidate,16modelcalls,25tool/35wallminutes,1infraretry;Vivado2025.2/xc7a35tcpg236-1/100MHz/idealzeroI/O. Retain failed attempts withoutreset. Only launch after21caseadmission andfrozenfullsuitepass. Independent exactsavedwinner/declaredchildren andactualDONE checks afterward. Measure nameddefault-instance arithmetic/q-r/reset/latency grader probes separately ifneeded; widthonlyfaults may be inapplicable atdefaultWIDTH8, neverclaimtheirabsenceascoverage. Fulltier0 again beforemainintegration; no higherheldtiercurrently.

## Evidence-driven harness correction: scoreboard example payload coverage

Divider01 completed26LUT/38FF,+.315/.129ns,31.58%LUTreduction; independent
exactwinner andDONE251 checks passed. Supplemental generatedgrader caught13/17
defaultfaults, missedzero_divisor_remainder_zero despiteexplicitaccepted
255/0=>R255 IOexample. Actualstimulus onlysimulated0/0. Originalmodeltrial and
13/17outcomes archived436files BEFOREchange. This is missing declared-input
coverage in RTL simulation, not an oracle arithmetic failure.

Plan: reuse current scoreboard engine. Preservecorners andseededrandomtail;
addunique completepayloadvectors fromeligible declaredacceptedexamples. Require
explicit inputvalid1 andresetdeasserted; skip partial/reset/inactiveexamples,
ignoreexampleoutready becauseTBowns scheduling. Validateexamples/boundedvalues
and total10000stepsincludingseeds/reset BEFORE allocations or oraclecalls.
Fixed-latency generation unchanged; no claimthatpayloadseedingreplaysstateful
after_cycles traces or closesreset/readiness faults. No newagent/engine.

Beforeimplementation: independentplanreview; tests for deterministicselection,
dedup/filter/renamedcontrols/activelowreset,bounds andno prevalidation sideeffects.
Afterfix: controlledactualsimulation withnewgeneratedTB,frozenqualifiedoracle
andunchangedreference/zeroRmutant; controlmustpass andpreviousmissmustassert.
Original01notresumed/regraded. Fullregression+freshfulltier0 onnewruntime before
mainintegration; runtimecohortstreakmustreset honestly. Researchbasis: existing
RESEARCH.md complementarygrader andprecise-evidence decisions; simplestdataflow
correction ratherthanrole/frameworkexpansion.

## October23: bounded previous-proposal feedback study (active)

Observed packet01 exact RTL repetition across all3 iterations, and divider01
iteration2 duplicate despite an accepted iteration1. Existing instruction and
current seed omit compact standard-flow outcomes. Keep current roles, cache,
budget and acceptance; add bounded prior completed iteration feedback only.
Preserve same RTL with distinct physical settings as a valid experiment.
Snapshot generated/repaired identities and standard metrics BEFORE Doctor;
project Doctor separately. Journal input/outcome and bind them at DONE.
Reconstruct local chronological records on replay; never read future design
history into an earlier proposal. Feedback cannot change any frozen contract.
Provide a frozen per-run optout for ablation; old saved configs default off.

Predeclared engineering tests: deterministic bounds, future exclusion, source
and script identity, infra/design distinction, rejected/accepted Doctor separation,
multiple candidates, repair identity, incumbent retention, interruption replay
without extra calls and modified/deleted feedback rejection. Fullsuite and fresh
fulltier0 after source freeze; no held higher tier exists.

Predeclared live study: three matched pairs on the admitted divider optimizer,
same frozen saved baseline RTL and independent6width TB, Vivado2025.2,
xc7a35tcpg236-1/100MHz idealzeroIO, N1/max3iterations/16calls/25tool/35wallminutes,
feedback off vs on, alternating order. Same CLI default route; actual model is
unknown unless emitted, so no controlled model-strength claim. No repeated
budget resets; retain every failure. Compare exact/codehash repetitions,
distinct verified candidates, accepted improvements, completion, model calls/
reported tokens and tool/wall seconds. Keep experimental feedback only if
repetition declines without reduced completion or material added cost; report
uncertain/negative results and revise/remove if benefit unsupported.

### Prelaunch amendment after invalid study01 setup

Study01 baseline was deliberately aborted before any paired result: combined
wrapper/core source conflicted with top-only generation guidance, spending
repairs restoring its missing helper. Raw plan/runtime/source, model calls,
tool logs and lower-bound budget remain in logs/proposal-feedback-study-01.
No outcome is used for feedback performance. Owned Python10212 tree stopped;
no other model/vendor/Python job remained. No source/budget reset or regrade.

Study02 uses only original generated parameterized core as editable top.
Frozen original wrapper is appended to supplied admitted six-width TB; only
TB container name changes to iterative_divider_core_tb, reversibly checked.
All original case/checker statements and wrapper are preserved byte-for-byte
after line-ending normalization. Same six selected configurations, pairedorder,
budgets and keep/remove criterion; all six actual paired runs still required.
This is a corrected experiment setup, not a relaxed acceptance requirement.


### Study02 decision and implementation gate

All six original rows and four actual restored DONE tamper probes are archived.
Predeclared context retention failed: repeated proposals did not decrease and
the quota interruption left usage incomplete. Set new advisory context default
off, retain explicit opt-in and immutable audit evidence.

Reviewed next changes: exact source dedupe; actual editable RTL supplied to
planner; seed-bound plans refreshed after accepted source changes; graceful
incumbent retention under the original planning budget. Record both observed
failures in taxonomy before source integration. Require full regression, a NEW
live run that actually exercises changed-seed replanning, independent winner,
actual DONE plan-binding tamper checks, and fresh full tier0 before main merge.
No old trial resume/regrade under changed runtime and no extra budget allowances.


Implementation gate: source binding/exact dedupe/default-off integrated;
1,340 full regression tests passed on203 frozen identities. First failed run
retained and execution-budget status restored without changing old regression.
Remaining acceptance: fresh actual accepted-source refresh, independent winner,
DONE plan-binding tamper proof, and fresh full tier0 before main integration.


Source-binding stage gates complete:1,340 full tests; actual accepted-source
fresh planning and exact independent winner; five DONE tamper probes; fresh
full tier0campaign10 passed2/2/newcohort/streak1. Integrate authorized main.
Next fixture proposal remains isolated until independent dot4 fault admission.


Dot4 complex design independently verified and archived651files. Next permanent
correction: explicit mechanical top timescale (actual controlled43-4099→685PASS,
zero modelcalls). Integrate reviewed tiny patch plus qualified fixture/pure tests
in one batch; taxonomy first, full regression and actual canonical topfirst check,
then one fresh final tier0 gate. Old complex run stays frozen, never regraded.


Permanent timescale+fixture stage:1,366 full tests and canonical13/13 actual
top-first admission passed. Final fresh tier0campaign11 remains before main.
The previously generated complex design remains verified on its original runtime.


October25: permanent wrapper timescale and complex fixture gates complete:
1,366 tests, canonical13-case top-first admission, fresh full tier0campaign11.
Integrate main; original complex experiment stays frozen on its prior runtime.

Next scoped design: elastic_dot4_build. One single-clock transparent child,
two elastic slots, eight unsigned8-bit operands,18-bit result, capacity2,
ready/valid, minimum output transfer age2; preserve full-rate retirement/
replacement and stable stalled results. Independent checker must distinguish
stage1 occupancy from output-valid and enforce exact availability, throughput,
reset abort at every occupancy and off-edge reset pulses. Qualify arithmetic,
overwrite/full/valid/stall/early/late/reset faults before generating RTL. Reuse
existing scoreboard and bounded roles; no protocol/framework expansion yet.


## October25: elastic_dot4_build admission and generated-build plan

Extend the verified arithmetic pipeline with two elastic slots and backpressure.
One transparent child elastic_dot4_core, eight unsigned8-bit operands,18-bit sum,
ready/valid, synchronous active-high reset, no parameters. Capacity exactly2.
Output is stage2-valid; stage2_ready=!v2||out_ready, stage1_ready=!v1||stage2_ready.
Stage1 captures17-bit partial sums on an accepted input; stage2 advances old
partials when ready. Earliest availability after edgek+1 for capture atedgek;
earliest handshake edgek+2, minimum transfer age2. Sustain one input/output per
edge after filling. Reset overrides transfers and clears both valid slots only
at rising edges; an entirely off-edge pulse has no effect. Hold valid output
payload during stall; invalid payload unspecified. All eight producer operands
remain stable while blocked. Golden maps one accepted tuple to arithmetic,
not pipeline occupancy/delay. No new framework or role is planned.

Prepare isolated spec/meta/reference/independentTB/faultmaterializer first,
then independent checker review. TB must model two slots and queue conservation,
pre-edge transfers vs post-edge availability, fill/full rejection, simultaneous
retire/advance/replace, bubbles/longstalls, all arithmetic boundaries and repeated
results, resets at stage1-only/stage2-only/both/stalled occupancy, and off-edge
reset pulses. Do not use FIFO occupancy!=0 as outputvalid.

Intended admission: passing control plus18 distinct compiling behavioral faults:
dropped product, signed arithmetic, pair/final carry truncation, early output,
late output, accept-full, overwrite blockedstage1, drop blockedstage1, clear
stalledvalid, corrupt heldoutput, duplicate retirement, lose full replacement,
throughput bubble, retainedstage1/reset, retainedstage2/reset, asynchronous reset,
and incorrect downstream-ready propagation. Compile failures/timeouts are not
assertion kills; preserve misses and input hashes before any checker correction.
Amend this plan explicitly before tool launch if fault definitions need revision.

After admission, fresh generated build with generated golden plus independent
TB, no qualification-reference seed. N1/max3iterations/16calls/25toolminutes/
35wallminutes/1infraretry; Vivado2025.2,xc7a35tcpg236-1,100MHz idealzeroI/O.
Freeze runtime/inputs before model calls, retain all failed attempts and costs.
Independently simulate exact savedwinner plus generated child; actual DONE
source/spec/plan integrity probes. Retain fixture on correct verified build even
without PPA gain; record DSP/fabric/timing/power together. Harness changes require
a reproduced gap, taxonomy first, tests and final regression gate.


### Elastic build01 exposed two concrete harness gaps

Qualified19/19 checker and frozen inputs remained unchanged. Firstactualbuild
failed beforeRTL: two oracle attempts, invalid signature copied from our own
prompt, then f-string rejected by unchangedrestricted interpreter. Preserve251
file failed-run archive before correction; original2calls are never reset.

Smallest prompt fix: syntacticallyvalid unannotated init/step scaffold; explicitly
document existing supportedPython subset, derive builtin/methodlists fromworker
policy, literalportnames. No interpreter/ALLOWED/retry/budget expansion. Tests
parse+validate scaffold, preserve oldresponse rejection and mode/reset/IOcontext.
Primarydesignbasis: existing RESEARCH workflow/interface decisions and Anthropic
Writing effective tools guidance; improve accurate API descriptions before adding
roles/tools. Runtime tests, not that article, establish our correctness.

Accounting audit: savedelapsed8.4238 precedes final10.31second completedmodelcall.
A clean module_failed return never checkpoints its final activewall time, losing
thatinterval on unchangedruntime resume. AddBudget.checkpoint usingexistingatomic
save, active-dispatch finally afterinput guards/DONEearlyreturn. Preserve call/tool
counts/schema/limits; testclean/handled/unhandled/gracefulinterrupt, pauseexclusion,
rawDONEreuse/tamper/inputguard budgetimmutability. Nohardkillatomicity claim.

Integrate both reviewed minimalfixes plus qualifiedfixture/puretests as onebatch;
taxonomyfirst; fullregression before NEWbuild-elastic-dot4-02 with byteidentical
spec/TB and original16call/25tool/35wall budgets. Neverresume/regradetheoldrun
underchangedruntime. Actualnewruntime requires finalfreshfulltier0 beforemain.


October25 elastic stage and harness fix gates complete: qualified19/19checker,
freshgenerated20LUT/4DSP/+.155/.206ns winner,852independentcycles,sixactualDONE
tamperprobes,1415fulltests,freshfulltier0campaign12passed2/2,newcohortheldfalse.
Integrateverifiedmain/development and checkcommittedarchives. Keep limitedPython
policy/dualverification/seed-boundplans/budgetdegradation; no newrole/framework.
Next design selection should test a distinct behavior (for example stateful
signed arithmetic under backpressure) and be planned/fault-qualified first.
Realboardprofile work needs exactboard/interface requirements; TARGETS defines
acceptance. Do not advertise arbitraryboardXDC/multiclock/hardwarevalidation or
formal/hardkillatomicity without implementing and measuring those capabilities.
