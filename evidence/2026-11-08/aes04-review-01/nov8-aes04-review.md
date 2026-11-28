# Independent AES04 outcome review — November 8, 2026

**Outcome: design attempt failed at `aes_round` RTL verification.** The round oracle advanced beyond AES03's oracle-construction failure, but none of four RTL candidates passed unit simulation. No full AES, integration, routed PPA, tier hold or board success was established. This ends the declared finite AES04 experiment; do not launch AES05 or continue task-specific prompt tuning.

Source: `8c59efb6289330b6ac1433c50da59f58e8b59f95`. Canonical run: `logs/explore-aes-20261108-04/aes128_core_build`; archive: `evidence/2026-11-08/explore-aes-20261108-04`. The JSON companion `work/nov8-aes04-review.json` records exact critical hashes, oracle statuses, latest process/log proof, configuration, prompt reconstruction and archive validation.

## Actual results and limits

| Stage | Retained result |
| --- | --- |
| Controller oracle | First attempt qualified against specification examples and generated stimulus |
| Controller RTL/unit test | First candidate passed ordinary simulation |
| Controller TB qualification | Unmodified control passed; `==` to `!=` mutant produced 103 `last` assertions, first at index 0; qualification established |
| Round oracle attempts 1–2 | Both rejected: `ValueError: ValueError: golden instruction budget exhausted (setup)` |
| Round oracle attempt 3 | Qualified; generated source builds a power/log table using 3 in the field modulo 283 (0x11b) |
| Round RTL initial + three repairs | All elaborated and ran; each retained simulation reports 102 `state_out` assertions, first at index 1, and `TEST FAILED: 102 errors` |
| Round TB mutation qualification | Not reached because ordinary round simulation never passed |
| Key-step / integration / synthesis / optimization | Not reached |

The final `run_summary.json` is `module_failed`, module `aes_round`, error `Testbench failures: FAIL index=1 signal=state_out (x102)`. The explorer's per-entry console records exit 1. The outer launch result records exit 0 because the supervising exploration completed and retained the failure; it is not a design pass. It reports 322.61 seconds overall; per-entry console rounds its duration to 314 seconds. Budget receipt records 9 model calls, 121.0498348 vendor-tool seconds and 313.1083487 active seconds. Those vendor seconds are compile/elaboration/simulation work, not evidence of synthesis/PPA.

Model-call count reconciles to four oracle replies (controller 1, round 3), two RTL generations, and three RTL fixes. Budget usage reports 106,606 input, 8,043 output and 48,384 cached-input tokens; no missing successful-call usage is reported. These are recorded usage fields, not a billed-cost estimate. Requested model is `gpt-6-luna`; this review does not establish a served-model identity or dollar cost.

Independent read/hash checks found all **343 frozen inputs unchanged**, and all **219 archive-manifest entries** match their bytes. AES03/AES04 frozen specification and integration-TB bytes are identical; compared model/device/flow/budget/iteration/repair/timeout configuration values are identical. The qualified CLI hash remains `4b3286e35d7fe866c6b0eb3f07d7a4cdb5e96489576170dfd6b3a15aa1c67382` in the launch receipt. Latest compiler, elaborator and simulator receipt rows for the inspected ordinary/control/mutant cases have actual and driver exits 0 with matching latest output hashes. Raw assertions, rather than nonzero simulator process exits, correctly determine these design failures.

## Hint/context delivery and repair quality

Reconstructed the actual `Generator.golden_model` rendering from unchanged source/specification and each retained round journal's keyword arguments, replacing dispatch with a capture stub. This makes no model call and does not execute returned Python. It is deterministic rendering evidence, not an independent network transport capture.

All three round prompts contain the general primitive-generator/complete-nonzero-coverage invariant, the explicitly qualified GF(2^8) count, the original S-box anchors and both public examples with zero omissions. Repair prompts contain the immediately previous oracle source, its matching rejection/file identity and actual setup-meter diagnostic without source truncation. Their character counts are 6,155 / 9,445 / 9,233. Both previous-source texts match their prior completed model journal entries exactly. The final oracle's chosen generator is mathematically suitable, but its source does not itself explicitly test full coverage or all inverse-product identities; do not claim complete compliance with every suggested self-check.

RTL feedback has a separate concrete limitation. Each fix receives its exact failing source and the same error containing index/signal/count. `roles.py:206–208` truncates the supplied 28,444-character TB text to its first 2,000 characters. That prefix does not contain the failing index's expected-value assignment, and the raw error contains no expected/actual values. All three build-module fixes receive an empty previous-error history (`fsm.py:899–900`). This explains what actionable feedback was absent; it does not prove that richer feedback would repair the design. Preserve it as a general diagnostic finding rather than opening another AES tuning cycle.

## Independent static defect diagnosis

All four retained round RTL candidates use the same erroneous inverse-exponent pattern. The final candidate's `candidate_standard_3/aes_round.v:40–45` starts `inverse = 1`, `base = value`, scans exponent bits from `i = 7` down to zero, conditionally multiplies using `(0xfe >> i) & 1`, and squares `base` each step. This combines descending exponent-bit traversal with ascending powers from repeated squaring: the selected powers are 1, 2, 4, 8, 16, 32 and 64, summing to **127**, whereas the intended inverse exponent is **254**. The defect is already present in candidate 0 and survives all three fixes. It is a static mathematical inference, consistent with the observed widespread S-box-related output failures; no generated Python/RTL was executed by this reviewer to obtain it. It is not a claim that every other RTL detail is correct.

This adaptive single-task sequence cannot attribute oracle recovery causally to the new hint, estimate general weak-model benefit, or establish benchmark superiority. The harness correctly rejected the observed failing RTL and retained its evidence. AES04 is a useful negative result with a narrower stage advancement, not completed AES or hardware proof.

Reviewer actions: canonical reads and trusted JSON/hash/diff/prompt-render calculations only. No canonical edits, tests rerun, generated-code execution, model/vendor/hardware calls, resume or launch. Board untouched by this review and launch receipt records `board_access: false`.
