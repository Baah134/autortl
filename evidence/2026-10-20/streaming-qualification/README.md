# Streaming verification admission

## Two-entry independent testbench: 9/9 expected verdicts

Real Vivado 2025.2 simulation: the supervised correct ring-buffer control passes;
eight compiling faults produce raw behavioral assertions and TEST FAILED.
Faults: capacity-one, overrun-ready, payload corruption, unstable stalled data,
dropped valid during stall, asynchronous reset, lost simultaneous-pop, and a
zero-cycle pass-through falsely annotated latency 1. No compile failure, watchdog,
missing log or infrastructure failure counts as a detected bug.

Control coverage:893 checked cycles, 679 accepted, 675 retired, 4 reset-discarded,
278 full cycles, 135 stalled cycles, 580 simultaneous transfers, 3 occupied resets.
Capacity and readiness are checked independently from a shift queue; the control
uses a ring buffer. All 256 payloads and 600 seeded cycles are exercised. This is
an 8-bit two-entry elastic queue with combinational ready, not registered-ready
isolation or a physical CDC result. Qualification references never seed generation.

Reproduce: python scripts/check_build_tbs.py --suite skid --bin-dir <Vivado/bin>
--output <fresh-output>. Unit tests for this runner are separate mocked-tool checks.
A generated streaming winner still needs its own independent verification and
routed results; qualification alone does not establish generation success.

## Serial-latency drain budget: 2/2 expected verdicts

A correct three-transaction device taking 100 cycles per operation was falsely
rejected by the former 168-cycle allowance. The reproduced short-budget TB differs
only in its loop limit from the corrected 368-cycle TB; same DUT SHA256 in both.
The corrected per-transaction allowance passes. The short-budget failure is a
known harness false rejection of a correct control, not a mutant kill. Both raw
logs, TBs and actual process receipts are retained. check_serial_latency.py is the
original local investigation helper (adjust ROOT when cloning elsewhere).

This finite test budget is not a liveness proof for unbounded stalls or arbitrary
initiation intervals. Minimum transfer age, ordering, payload stability and the
independent queue's exact capacity/readiness remain separate checks.

Compiled simulator trees and duplicate journal artifacts are omitted. Absolute
paths in receipts refer to original local runs. Archive manifest identifies retained
bytes; these folders are evidence subsets, not resumable execution directories.

Full regression suite for the serial/reset budget changes: **746 passed in272.44s**.
