# Frozen generated signed FIR grader audit

Status: **completed**. Reference passed: **True**.
Generated unit grader detected **18/27** named faults;
**9 misses**, **0 ungraded/not executed**.
The independent admitted checker detected the same27faults on identical RTL.

Misses: truncate12, history_on_invalid, stale_history_reset, async_history_reset, retained_stage1_reset, retained_stage2_reset, retained_stage3_reset, async_valid_reset, combinational_reset_gate.

All27 planned faults remain in the denominator. Only actual assertions with
successful compilation/elaboration/simulation process receipts count as detections;
compile errors and watchdogs do not. Raw per-case outcomes are retained.
Diagnostic wall time 344.062 seconds, actual tool-process
time 319.626 seconds; zero model/synthesis calls.
The original generated experiment, its fileset/budget/router records and227source
identities stayed unchanged. This audit does not regrade that experiment.

See [original generated design](../generated-signed-fir4-attempt-01/README.md)
and [independent admission](../../2026-10-25/signed-fir4-admission-attempt-01/README.md).
These are selected simulation-fault sensitivities, not formal equivalence or
an arbitrary-model reliability comparison. Original grader/stimulus/golden
identities and all outcomes are frozen before any later correction.
