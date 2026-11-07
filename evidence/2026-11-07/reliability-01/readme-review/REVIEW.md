# README claim corrections — isolated proposal

This proposal changes only the public README. It keeps the pitch, result tables, diagram and usage intact and introduces no new measured result or coordinator checkpoint. Canonical README was not edited.

Files: `README.before.md` preserves the original raw bytes; `README.md` is the proposed text; `proposal.patch` is self-contained against `a/README.md`; `link-check.json` records local link validation. Generator: `../prepare_nov7_readme_stage.py`.

Canonical base SHA256: `914513321ce81e957bdbedefe86dcb5f6b63adb5c2f0b7b6f078d64fc9b3e13a`.
Patch SHA256: `c15b10f87717d1a75d0f5f5bd75498a2d60a15d66283e47e61d931ec50004ac9`.

## Claim-to-evidence map

Paths in this table are relative to the canonical repository. These are retained past results, not new board tests.

| Corrected claim | Local evidence | What the proposal establishes |
|---|---|---|
| Retained candidates pass static checks, compilation and qualified simulation; timing progress is distinct from a resource-saving win | `autortl/fsm.py`: `_verify_optimization_candidate` and optimization selection at1178–1229; `autortl/objectives.py`: `timing_progress`, `improvement_kind`; `tests/test_optimizer_recovery.py`; `tests/test_feasibility_policy.py` | A candidate needs five ladder rungs and validated process exits before selection. The evaluator can veto. `timing_progress` can replace an infeasible incumbent after improved setup slack and the hold policy; it stays `timing_closed=false`. A feasible incumbent cannot be replaced by an infeasible candidate, and objective/resource gains require feasibility. The intro no longer claims every working-best update meets timing. |
| Planner-generated specifications can be repaired; optimization contracts and supplied typed specs remain fixed | `autortl/fsm.py`: `_run_build` at514–650; `autortl/roles.py`: `Planner.make_spec`; `_verify_optimization_candidate`; `docs/DESIGN.md` | A supplied JSON spec fails immediately on lint errors. Prose-derived specs have bounded structural/example repairs; oracle disputes can create a recorded spec revision and rebuild all modules. During RTL optimization, candidates cannot redefine the current interface/reset/latency or acceptance inputs. Intro, role overview and fixed-contract bullet now agree. |
| Generated cores, independent handwritten shells, distinct simulation/standalone/hardware records | `hardware/basys3/harness_winners/README.md`; `evidence/2026-10-28/basys3-harness-winners-01/README.md`; `evidence/2026-11-02/basys3-tier46-board-01/README.md`; `evidence/2026-11-02/basys3-tier56-board-01/README.md` | Removes the blanket statement that everything below—including AXI4-Lite, arbiter and verifier results—was run on a board. The twelve named cores have hardware records; human-written integration is acknowledged. |
| UART child RTL is unchanged; board integration and baud values are handwritten | `evidence/2026-11-01/basys3-harness-echo-01/README.md`, especially Board parameters; `hardware/basys3/harness_built/uart_echo_all/board/rtl/basys3_harness_echo.v` | The wrapper instantiates archived children directly and repeats top wiring with OVERSAMPLE_DIV54/CLKS_PER_BIT864 and qualified FIFO depths. Saying the complete link was wired together unchanged hides this adaptation. Existing1,000,000-byte result remains unchanged and linked. |
| Twelve cores each passed50,000 transactions under randomized backpressure at100MHz | Three board archives listed above; `hardware/basys3/harness_winners/README.md` design/status table | Adds direct evidence links to the headline. The claim refers to archived cores in a handwritten shell, not autonomous board bring-up or new testing on today's attached board. |
| FIR16 closes150MHz out of context; physical validation uses100MHz | `evidence/2026-11-02/fir16-ooc-02/README.md` (target150MHz;394→148LUT;+0.751ns finalWNS); `evidence/2026-11-02/basys3-tier56-board-01/README.md` (Build at100MHz); `fir16_sym/summary.json` under that archive (WNS3.066ns;50,000/50,000;zero mismatches) | Clarifies the highlight, result-row verification and blanket timing sentence. A100MHz physical run does not demonstrate150MHz operation on the board. Existing standalone and board metrics are not combined. |
| More than2,000 harness regression tests, with a named receipt | `evidence/2026-11-02/signoff4-t6-01/signoff4-t6-01-tests.json`: exit0,2022passed,334source unchanged | Replaces the unscoped2258aggregate. Shared memory identifies that historical total as2021harness+237tooling at8abd6eb9; the new text neither adds suite counts nor pretends the historical total is a fresh test run. It remains valid after small future test additions. |
| CI audits bindings and preserves historical losses | `.github/workflows/tests.yml` evidence job; `docs/PUBLICATION.md`; `tools/evidence_exceptions.json`; root's `work/nov6-signoff-audit.json` atb59d077c (166275claims,171accepted_loss,138excepted) | Removes the stale34000count and avoids implying every historical byte survives. No new audit headline number is added to README. |
| Recorded tier0 hold is historical | `evidence/2026-10-29/contract-campaign-17/README.md` | Wording says 'A recorded tier0hold' rather than implying this old campaign holds arbitrary subsequent runtime changes. Keeps the existing linked historical result. |
| Public-task improvement over a single model invocation is unmeasured | `docs/ACTION_PLAN.md`, Benchmark protocol; `evidence/2026-11-06/parallel-diagnoses-01/nov6-benchmark-protocol.md`; `evidence/2026-10-29/model-matrix-01/README.md` | The four-model matrix is exploratory on two tier0tasks, without a no-harness baseline. README adds one short honest scope sentence; it contains no pending coordinator tasks or benchmark plan narrative. |

## Validation

- Twelve narrowly scoped text substitutions; no RTL, runtime, constraint, result or gate changed.
- **64 relative Markdown link targets exist**, zero missing. Checked against the canonical repository. Remote GitHub badge/action status was not fetched; the badge is unchanged and explicitly targets main.
- Existing Mermaid diagram remains unchanged. No video or screenshot asset is invented or added.
- Canonical README raw bytes still match the base SHA256 after stage generation. Parent must recheck that SHA before integration if another agent edits the file.
- No regression or vendor/model job was warranted for this text-only proposal. No board access occurred.

## Timing and specification follow-up resolved

Parent requested the initial timing/immutable-spec risks be closed in this same isolated proposal. Exact FSM behavior was inspected before wording changes. Importantly, evaluator `ACCEPT`, `is_best=true` and final `status=done` can all occur while a candidate remains timing-infeasible. The README therefore says **resource-saving wins** require setup/hold closure and describes explicitly labelled **timing progress** separately; it does not claim every internal ACCEPT or DONE means closure. `curriculum/runner.py` applies timing criteria to completed design results. This documentation change does not rename runtime statuses or weaken any gate.

The new text also avoids presenting a role's limited prompt view as an operating-system sandbox. The later BYO section continues to state that arbitrary user-selected command endpoints are not sandboxed by AutoRTL.
