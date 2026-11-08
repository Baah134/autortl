# Finite-field guidance: staged change and evidence

Only `autortl/prompts.py` and the new
`tests/test_golden_field_guidance.py` differ in this isolated proposal.
Canonical runtime files remain unchanged. The new wording qualifies the
existing log/antilog suggestion with its necessary mathematical preconditions:
primitive generator for the specified field, all nonzero elements before
repetition (255 specifically for GF(2^8)), and field-product inverse identities.

The production prompt contains no selected numeric generator, implementation,
lookup table, AES answer or new runtime acceptance check. It does not ban a
generator across all fields. The original sandbox, module-boundary instructions,
context mechanism, three attempts, budgets and role count are preserved.

## Verification

Accepted baseline: **2 failed, 6 passed in 1.39s**, exit 1. The two failures are
actual initial/repair prompt-delivery assertions. All six independent arithmetic
controls already pass before the prompt change; they establish the validity of
the proposed invariants, not an implementation improvement.

After: **112 passed in 88.50s**, exit 0, across field-guidance, golden prompt,
oracle context, module-local context, recovery, hardening, reset protocol,
role-conformance and specification-dispute suites. This result is for V1.

Final V2 only qualifies the coverage count explicitly to GF(2^8) and adjusts
the delivery assertions. Its eight affected tests passed in 0.92s, exit 0.
`receipt-v2.json` records final raw-byte input and patch hashes, exact commands,
the V1 focused result and raw logs. `proposal-v2.patch` is the final review
patch. Both old and new source text are normalized only for that readable
diff; the staged prompt preserves CRLF. Immutable V1 sources, receipts and both
the original and readable V1 patches are preserved with hashes in V2 receipt.

The arithmetic controls use polynomial convolution and reduction, without
executing generated programs. They distinguish the deficient 51-element walk
for one field from full 255-element walks in that field and another field.
The different-field control makes a blanket ban on a particular generator
incorrect. Complete inverse-product checks exercise all nonzero bytes for both
valid walks. Numeric choices appear only in tests and engineering evidence,
not in the production prompt.

One initial staging-helper newline match failed after a successful baseline:
the helper expected LF while the source used CRLF. `before-tests.txt` preserves
that first baseline. The helper was corrected to retain the original newline
bytes; `before-tests-v2.txt` is the final baseline. No prompt was changed before
the corrected helper proceeded, and no canonical file was touched.

## Limits and experiment boundary

These are instruction-delivery and deterministic arithmetic tests. No model
call, vendor-tool run, server initialization, board access or design success
occurred in this stage. The mathematical background and independent exhaustive
probe remain in `work/nov8-gf-guidance-assessment.md` and its referenced files.
They supply public definitions and derived checks, not production answer code.

The coordinator must record acceptance/taxonomy before canonical integration,
review this exact patch, run complete software checks and publish/freeze it.
At most one fresh AES04 experiment may then use the original contract and
budgets. Preserve every outcome; do not start AES05 or keep tuning this task
after that declared experiment. No causal, held-out or general model-superiority
claim follows from this staged result.
