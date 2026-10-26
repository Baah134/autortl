# Signed FIR4 stream: isolated admission proposal

This fixture exercises signed, accepted-sample history together with a three-slot
elastic pipeline. It is prepared for review, **not yet tool-qualified**. Neither
the control nor the 27 faults has been compiled or simulated in this stage.
There is no generated implementation or measured PPA result yet.

## Contract

`signed_fir4` transparently wraps one `signed_fir4_core`. Ports are `clk`, `rst`,
signed8 `x`, `in_valid`, `in_ready`, signed13 `out_data`, `out_valid`, `out_ready`.
There are no parameters. Each accepted sample produces
`3*x[n] - 5*x[n-1] + 7*x[n-2] - 2*x[n-3]`, with three initially zero historical
accepted samples. The exact range is [-2169,2166]; saturation is forbidden.

Capacity is three. Ready propagates backward through empty or advancing slots.
Capture at edge k reaches the final slot after edge k+2 and cannot transfer
before edge k+3. The full pipeline must retire and replace one token each cycle
when unobstructed. A blocked valid output remains stable. Synchronous active-high
reset overrides transfers and clears history/valids at the edge only. Invalid
output payload is unspecified. Off-edge reset pulses have no effect.

The generated golden must model accepted samples and history only. IO examples
restart state independently; `after_cycles` repeats the same accepted tuple and
is not an RTL pipeline age. External signed values use masked integers.

## Independent verification

The qualification reference captures two signed partial sums, combines them in
stage two, and registers stage three. The independent TB computes the complete
integer FIR expression from its own accepted history. Abstract whole-result
slots check exact pre-edge and post-NBA ready/valid/data; a separate FIFO tracks
ordering, capture age, retirement, reset abort, and conservation. The oracle
uses expected readiness after checking DUT readiness. The producer preserves
actual blocked valid/data, except when reset aborts it.

Directed coverage includes both-sign impulse tails, alternating extrema forcing
13 bits, changing invalid data, nonzero-history stalls, full simultaneous
replacement, all seven nonempty reset occupancy masks, and off-edge pulses with
history-only and full blocked pipelines. Ports are checked during pulses.
Deterministic seeded random traffic follows directed traffic and ends in drain.
Required coverage and checker/watchdog failures have distinct messages. Only raw
`FAIL BEHAVIOR rule=...` assertions may establish a behavioral mutation kill.

## Admission cases

`qualification/cases.py` exposes `case_sources()` and `materialize_cases(output)`.
It rejects existing output directories and emits reference first, followed by
27 distinct faults, each with `children.v`, mechanical `signed_fir4.v`, and the
same `signed_fir4_tb.v`. The manifest records file hashes and edit targets.
The simulation top is `signed_fir4_tb`; compile the wrapper first as usual.

Faults cover coefficients/tap order, unsigned interpretation, 12-bit truncation,
invalid/blocked/delayed/reversed history updates, stale/asynchronous history
reset, early/late output, illegal acceptance, stage overwrites, stalled validity
and data, lost replacement, throughput bubbles, each retained reset slot,
asynchronous valid reset, wrong downstream readiness, and combinational reset
gating. Retained history/valid faults initialize cleanly at startup, so they
must fail occupied/nonzero-state behavior rather than initial unknowns.

Admission requires the reference to pass and every planned fault to compile,
elaborate, and produce a real behavioral assertion. Compile errors, timeouts,
coverage-only failures, and checker errors do not count. Preserve misses and
all frozen inputs before changing any checker; do not reduce the denominator.

`pure-validation.json` records structural checks only. It does not establish
Verilog compilation, coverage completion, mutation kills, or synthesis results.
The reference is exclusively an admission control, never a generation seed.

The concrete `incorrect_downstream_ready` fault substitutes `in_valid` for
`out_ready` in final-slot readiness (`r3`), corrupting backward ready propagation.
