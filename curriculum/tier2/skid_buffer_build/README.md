# Two-entry elastic streaming buffer

A build task for an eight-bit, two-entry FIFO with ready/valid flow control.
`in_ready` is combinational from occupancy and `out_ready`; this fixture does
not claim registered-ready isolation. There is no empty-queue bypass. A newly
accepted word becomes visible after its capture edge and can transfer at the
next edge. Reset is synchronous and discards queued words.

The typed RTL contract specifies full cycle-level queue behavior. Its Python
scoreboard oracle has a separate job: map each accepted input payload to its
identical eventual output payload. It must not model occupancy or backpressure;
the scoreboard schedules those handshakes. Examples include active transfer
controls and expected data only.

`skid_buffer_tb.v` is the independent top-level authority. It uses a shift queue,
checks outputs before and after edges, verifies exact readiness/capacity and
nonempty validity, and ignores output data when invalid. Directed and seeded
random phases cover full backpressure, simultaneous transfers, bubbles,
throughput, repeated filling/draining, stalled output stability, and reset while
occupied. The producer holds pending data until accepted. Coverage counters and
a watchdog prevent an unexercised or nonterminating test from passing.

`qualification/` contains a ring-buffer reference and behavior mutants solely
for testbench qualification. They are not a generator seed and are not listed
as the design in `meta.yaml`. `qualification/cases.py` can materialize standalone
simulation cases plus a SHA-256 manifest. It launches no tools.

## Evidence status

Fixture/schema/static/unit validation does not establish simulation success.
The reference and every mutant still require real simulator qualification:
reference must emit `TEST PASSED`; mutants must emit a behavioral `TEST FAILED`.
A reset-gated combinational passthrough mutant deliberately retains `@latency 1`:
matching an annotation is not independent proof of cycle-level behavior. The
independent TB checks an empty queue before capture to detect that bypass.
Compilation/elaboration errors, missing verdicts, timeouts and infrastructure
errors are not mutant kills. No synthesis result, optimization gain or held-tier
claim follows from adding this fixture.
