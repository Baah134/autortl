# FIR coverage-runtime full regression01

Actual complete regression: **1450 tests passed in 457.63 seconds**.
The launch receipt records 459.187 seconds of actual
wall time. All230 source identities remained unchanged; the retained source
snapshot matches the exact freeze bound by the passing launch receipt.

This batch covers signed temporal extrema and legal scoreboard bubbles,
invalid payload noise and sync-only off-edge reset pulses. Focused passing
tests and original failing regressions are retained alongside integration
receipts. Related-evidence manifest hashes link the separate old generated
grader audit, signed-boundary comparison and full driver comparison without
rewriting those outcomes. See result.json for measured counts and references.

These are software regressions, not a new FPGA result. Fresh generated build02
and the full tier0 runtime gate require their own actual results. No formal,
general reset-coverage, board-validation or weaker-model claim follows.
