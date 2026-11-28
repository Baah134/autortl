# Public-example and matched-repair context study

Status: isolated Phase2 proposal after AES02 repeated oracle failures. No
canonical edits or model/vendor/board action by this worker. Root coordinates
integration and any actual fresh trial.

## Why this mechanism is now justified

AES01 and AES02 both exhausted three oracle attempts for the controller before
RTL generation. AES02's rejected programs still recomputed neighbor functions;
its failures were unsupported .extend and two setup-budget exhaustions.
Phase1's generic boundary/helper instruction was reconstructed in all three
application stdin strings from frozen implementation and journaled arguments.
No application-side truncation or prompt cache exists in that path. The original
CLI stdin/JSONL/server receipt is not retained, so actual wire receipt/attention
is unknown. System conventions do not instruct this controller to model neighbors.

Two concrete omissions remain: public ModuleSpec.examples never enter the oracle
prompt; the repair call has only a truncated error, without the failed program.
Expected-vs-actual mismatch text alone omits the generating input/state trace.
Repeated unrelated rewrites are consistent with this limitation, but do not
prove causation. CLI changed from0.166 to0.167 between AES01/02, so the trials are
not a controlled measurement of Phase1 effectiveness.

## Minimal change and limits

Only roles.py and fsm.py change. The role adds whole public examples containing
their original index, inputs, expected values and after_cycles; each starts
from fresh init, repeats identical inputs for that many calls to step, and
compares the final output. Scoreboard calls remain accepted transactions rather
than physical clocks. Rendered examples have an8000-character ceiling and at
most64 entries inspected; omitted records are counted explicitly, never cut
into partial JSON. No hidden testbench, golden reference field or admission RTL
is supplied.

For repairs only, the local module loop passes its immediately preceding source
and recorded failed-file SHA256 alongside the matching latest diagnostic. The
role labels the previous source as untrusted artifact data, preserves a separate
SHA256 for the full provided UTF8 source text, and emits at most12000 characters
of artifact JSON plus a fixed explanatory header. It uses explicit original and
shown character counts and truncation status. Raw Windows file line endings can
differ from prompt text; the two digests are not conflated.

The first oracle call carries no stale repair context. The call API adds optional
keywords; existing call forms remain valid. The three-attempt ceiling, initial
and shared-step meters, generator model, declared contract/examples, qualification
and acceptance rules do not change. No sandbox method is added. Provider and
storage failures propagate; no hidden retry or extra generation call is added.

## Software acceptance

New tests exercise actual role prompt delivery, public examples and omissions,
untrusted bounded artifacts and separate identities, successive source/error/raw
digest pairing, module-local state, no new calls on journal replay, and existing
provider/storage propagation. Existing oracle recovery/hardening/reset/prompt,
Phase1, role-conformance and spec-dispute suites are part of the focused run.

The first replay-control fixture failed because journal-enabled qualification
was not mocked. It attempted the unavailable xvlog launcher; no vendor process
started. The original logs are retained as initial-before/after-fixture-error,
not counted as evidence of the production bug. The new fixture now stubs both
qualification entry points. No existing test file was weakened or modified.

## Fresh same-budget measurement after integration

Freeze the reviewed implementation, all public spec/example hashes, independent
integration checker, CLI executable/version, requested model and metadata limits.
Use a new AES03 directory; never resume/regrade AES02 or reset its budget. Keep
one entry/job, original30-call/150-tool-minute/240-wall-minute/4-iteration/N1
ceilings and the existing three-attempt oracle rule. No board programming.

Record each oracle source/error/outcome and whether source/error binding matches
the raw receipts. Retain every attempt, budget/token/time usage, unknown price
or observed-model fields, independent-control verdicts and actual process exits.
Separate oracle qualification, RTL build, independent simulation, timing and
optimization results. A qualified oracle or launcher exit0 is not AES success.

A fresh completion would demonstrate this particular pipeline execution; it
would not identify whether examples, repair context or sampling randomness caused
the change. If a causal success-rate/cost claim is required, preregister a matched
multi-trial comparison on the same observable backend/CLI/version with identical
contracts and ceilings. Public examples/source-context ablations must keep the
same independent final grader and record increased input-token cost. Unknown
actual model identity limits provider-controlled conclusions.

Keep the mechanism if it supplies the missing contract/artifact context correctly
without regressing safeguards; do not report general model improvement before
measuring it. If AES03 still fails, classify its actual first failure instead of
adding retries, reference code, an AES-specific correction or a new agent role.
