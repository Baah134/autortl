# Proposed two-stage elastic dot-product fixture

Isolated proposal only. No compilation, simulation, physical implementation,
model calls or fault admission have been performed for these sources.

## Contract

One transparent child `elastic_dot4_core` behind top `elastic_dot4` computes
`a0*b0+a1*b1+a2*b2+a3*b3`. Eight operands are unsigned 8-bit, partial sums
are 17-bit and result is 18-bit, range 0..260100. There are no parameters.
All operands are ordinary data ports; exactly four controls are marked
`valid_ready`: in_valid, in_ready, out_valid, out_ready.

The two slots have valid bits v1/v2. Output valid is v2, not total occupancy:

```
ready2   = !v2 || out_ready
in_ready = !v1 || ready2
out_valid = v2
```

At a rising edge, ready stage2 takes OLD stage1 validity and partial sums;
ready stage1 takes the current input-valid and accepted operands. Capture at
edge k becomes available after edge k+1 when advancement is possible. Earliest
retirement is edge k+2. Scoreboard latency 2 means minimum transfer age, not
fixed completion time under stalls. Full simultaneous retire/advance/replace
must sustain one transaction each edge. Capacity is exactly two transactions.

Synchronous active-high reset clears both slots and overrides transfers only
at rising edges. Entirely off-edge pulses do nothing. Valid stalled output
must remain stable; invalid payload is unspecified. A blocked producer holds
valid and all eight operands until acceptance, except reset abort.

Golden semantics: one accepted tuple maps to its eventual mathematical sum;
do not implement a pipeline, validity, occupancy or scheduling in the oracle.
The transparent top may inherit the known child's minimum-age annotation.

## Independent verification

The checker stores whole mathematical results in two abstract slots, unlike
the reference RTL's pair partial sums. A separate queue records order and
capture edges, checking age and conservation. It checks outputs before the
edge and again after NBA settlement, including exact readiness and availability.
Driver retention uses actual DUT input acceptance so all eight operands remain
stable when blocked. Reset explicitly cancels pending producer work.

Directed traffic covers all individual products, unsigned high bits, carries,
zero/max, asymmetric inputs, repeated results, fill/rejected third input,
full simultaneous replacement, long stalls and drain. There are 256 additional
directed tuples and 500 deterministic random cycles. Reset covers stage1-only,
stage2-only, both slots and stalled output. Off-edge pulses at stage1-only and both-slot occupancy are followed
by subsequent state checks. Coverage counters and watchdog gate the final verdict.

The stage checker deliberately does not assert FIFO-style out_valid=nonempty.
Accepted equals retired+reset-discarded+outstanding; at final drain outstanding
must be zero. Defined payload checks use case inequality to reject X values.

## Intended admission: one control and 18 faults

`qualification/reference.v` is an independent admission control, never a model
seed or generated winner. `qualification/cases.py` defines these exact faults:

1. Dropped product.
2. Signed arithmetic.
3. Pair carry truncation.
4. Final carry truncation.
5. Early output-valid from stage1.
6. One-edge late output-valid.
7. Accept while full and blocked.
8. Overwrite blocked stage1.
9. Drop blocked stage1.
10. Clear stalled output-valid.
11. Corrupt held output.
12. Duplicate retirement by retaining stage2-valid.
13. Lose an accepted full replacement.
14. Insert a full-replacement throughput bubble.
15. Retain stage1 across reset.
16. Retain stage2 across reset.
17. Asynchronous reset.
18. Propagate input-valid instead of downstream-ready into stage2 readiness.

Every edit target must occur once and every resulting source must differ.
The materializer writes fresh control/mutant/unchanged-TB/wrapper inputs with
raw-byte hashes. It does not launch tools. These faults are intended to compile;
only actual admission can establish that fact and the expected behavioral kill.
Admission requires BEHAVIOR_FAIL plus successful compilation/elaboration and
completed simulation. COVERAGE_FAIL, CHECKER_FAIL and watchdog-only outcomes
are not behavioral kills. No compile error, timeout, missing verdict or
infrastructure failure is a kill.
Preserve failed admission inputs and coverage misses before changing a checker.

## Review risks and acceptance sequence

- Review pre-edge vs post-edge ordering and the first-valid/first-transfer
  distinction. Queue and slot references agree independently on occupancy.
- Coverage thresholds and all 18 expected kills are unverified until simulation.
- Readiness faults can affect later producer traffic; retain the first concrete
  readiness/availability assertion, not only a subsequent watchdog or coverage miss.
- Reset-retention mutants initialize unknown/empty valid state to zero using
  procedural if/else, but retain occupied state across later reset edges. Thus
  they target occupied reset abort rather than failing only initial X cleanup.
  This definition was refined before source freeze or any admission experiment.
- Generated scoreboard covers arithmetic/order/minimum-age/stall checks, but
  independent exact availability, capacity and throughput checks remain necessary.

Root review precedes source freeze and actual admission. After all 19 cases
meet their expected verdicts, use a fresh bounded generated build with generated
golden plus independent TB: N=1, at most 3 iterations, 16 model calls,
25 tool minutes, 35 wall minutes and one infrastructure retry. Use the existing
Vivado/device/100 MHz ideal-zero-I/O experiment constraints. Independently replay
the exact saved winner and check DONE integrity. Correct build is meaningful
without PPA improvement; disclose DSP, LUT, slice-FF, timing and power together.
Any harness change requires a reproduced gap, taxonomy and regression evidence.
