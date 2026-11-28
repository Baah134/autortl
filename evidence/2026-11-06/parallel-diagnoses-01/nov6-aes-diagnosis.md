# November 6 AES oracle diagnosis (read-only runtime review)

Reviewed canonical e61665c53552788f6d3690f4f1ddb8a94fecad93. No canonical edits, leases, tests, model calls or vendor jobs. Active freeze contains 334 files. This document records source inspection, not a new execution result.

## Observed failure chain

Evidence root: C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t6-01/tier6_je4m8_82/aes128_core_build/.

The three modules/aes_round/golden_attempt_N.log receipts and journal/*/completed.json stage module_aes_round:model:generator.golden_model:0..2 preserve three different oracle programs:

1. Attempt 1 executed but failed specification example 0. Its MixColumns row 1 uses a0 ^ x1 ^ a2 ^ a3, omitting x2 from the required coefficient 3*a2. Rows 2 and 3 similarly omit the extra doubled term for coefficient 3. This is a concrete generated-program error, not evidence that the specification is inconsistent. Recorded source SHA256 73ac0b9f9e60ead49f4824e83355e738a9d65179e66e52451d8ba3932c5d63e6.
2. Attempt 2 replaces the algorithm with per-byte square-and-multiply inverse generation. It is rejected by the existing setup instruction budget. Recorded SHA256 25c70cec4ed43f016bf495a4a6614047dade3781309f117a9e0eede81c5b157a. This program uses the strategy the current prompt explicitly offers, but its particular implementation exceeds the meter; no evidence establishes that all efficient square-and-multiply implementations must fail.
3. Attempt 3 uses a 255-element exponent table, then indexes exp_table[255-log_table[byte]]. For byte=1, log_table[1]=0, requesting nonexistent index255. Recorded SHA256 501fcafcc8fa286ae08e8bd5503ad92cafcbbc7185493f3499cd182383adfed8. This follows directly from the saved program and agrees with the IndexError receipt. The first attempt had a repeated exponent-table tail; the final rewrite lost it.

The entry properly ends module_failed. This is not an RTL/synthesis failure or an incorrect acceptance. CORDIC and RV32I pass, leaving tier6 at 2/3, below80%.

## Existing mechanisms and concrete limitation

- autortl/fsm.py:788-843 bounds oracle generation to ORACLE_ATTEMPTS=3, writes each rejected source digest/diagnostic, and supplies only the latest bounded error string to the next call. The completed journal retains each extracted source even though golden.py is overwritten.
- autortl/roles.py:163-176 golden_model assembles a fresh stateless prompt from module behavior/ports and appends feedback; it does not include the failed Python source. Thus "Repair this specific failure" supplies no actual program to repair. The observed successive algorithm replacements are consistent with that limitation, though this single trial cannot prove causation or improvement from a fix.
- autortl/prompts.py GOLDEN_MODEL already instructs efficient table construction once in init, gives restricted API rules, and recommends checking stated example table values. No new AES algorithm or reference answer is necessary.
- autortl/golden_worker.py uses separate setup and shared-step budgets, both 2,000,000 instructions. The observed budget rejection is working as designed. Do not increase budgets from this one failed trial.
- Supplied JSON specs are not planner-rewritten. A three-error chain of mismatch, resource exhaustion and index failure is not the repeated example-only dispute path.

## Smallest warranted proposal, after current run settles

First inspect the already-started signoff4-t6-02 outcome. At this review its console contains only the source-freeze line; logs/signoff4-t6-02 does not exist and no test/verdict receipt is present. A CIM query was denied, so liveness is unknown. Do not launch a competing run or edit frozen runtime.

If AES failures recur, propose a bounded generic repair-context change: pass the previous generated oracle source plus its matching diagnostic to golden_model on repair attempts, clearly delimited as untrusted program text. Preserve initial-call API behavior, attempts, charging, sandbox, examples and verdicts. Bound source size and explicitly label truncation; source/digest must agree with the recorded failed attempt. This makes the existing repair instruction actionable without supplying qualification-reference code. Avoid claiming this will improve pass rates until a controlled fresh experiment measures it.

Minimum regressions: capture initial prompt (no stale source); capture sequential repairs and require each contains exactly its immediately preceding source/error pair; verify rejection sources are not mixed between modules; exercise journal replay without extra model calls and correct source/feedback binding; preserve three-attempt exhaustion and provider/timeout propagation. An existing public-spec example mismatch and an intentionally out-of-range toy table are sufficient generic fixtures. Historical AES programs may remain negative cases; do not add their corrected AES implementation to generator prompts.

Independent small follow-up: review whether prompt guidance about efficient table setup needs tighter operational wording, but do not add algorithm-specific patches merely to make this failed sample pass.

## Priority

1. Resolve current gate process ownership and collect t6-02 receipts without mutation.
2. Preserve all campaign outcomes; if the current runtime succeeds, finish declared signoff before scheduling harness experiments.
3. If failure repeats, archive before proposing the generic source-grounded repair study above. No budget escalation, retroactive regrading or reference-code injection.
