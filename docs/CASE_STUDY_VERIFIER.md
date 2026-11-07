# Case study: auditing the generated verifier

AutoRTL's generated unit grader accepted a correct signed, stateful four-tap
FIR—but also accepted nine deliberately faulty implementations. Auditing the
grader exposed gaps in stimulus coverage and reset observation. Small changes
to the deterministic driver increased detection from **18/27 to 22/27**;
the five remaining misses stayed explicit.

| Checker | Faults detected | Missed | Ungraded |
|---|---:|---:|---:|
| [Original generated grader](../evidence/2026-10-26/signed-fir4-generated-audit-01/audit/result.json) | 18/27 | 9 | 0 |
| [Corrected generated grader](../evidence/2026-10-26/fir4-driver-comparison-01/comparison/result.json) | 22/27 | 5 | 0 |
| [Independent FIR contract checker](../evidence/2026-10-25/signed-fir4-admission-attempt-01/admission/result.json) | 27/27 | 0 | 0 |

All three passed the correct reference. The same 27 named RTL faults remained
in the denominator; compilation failures, simulator crashes and watchdogs did
not count as detections. The independent checker's 28 admitted cases include
one passing reference and 27 faults detected through behavioral assertions.

## What the audit changed

The deterministic stimulus and testbench generator lives in
[tbgen.py](../autortl/tbgen.py).

**Exercise arithmetic limits across accepted history.** The original generated
traffic produced expected FIR outputs between −1703 and 1539, leaving a signed
12-bit truncation bug invisible. Six alternating minimum/maximum signed payloads
extended that range to −2169 through 2166, crossing the 12-bit limits. The
correct reference still passed; the identical faulty RTL now triggered five
`out_data` assertions. The same Python oracle calculated expectations, while
the original corner/example prefix and 100 seeded random inputs were preserved.
([Controlled comparison](../evidence/2026-10-26/fir4-signed-boundary-comparison-01/comparison/result.json))

**Distinguish offered data from accepted data.** Legal input-valid bubbles now
carry changing invalid payloads. This exposes a history register that updates
when ready is high even though no transfer occurred. A blocked producer retains
its valid and payload using the **previous rising edge's** handshake; recomputing
that decision after changing downstream ready can itself create illegal traffic.

**Observe synchronous reset between clock edges.** Bounded reset pulses begin
and end between rising edges, with other inputs held stable. Erroneous
asynchronous history/valid resets then corrupt later checked behavior. The
driver leaves the oracle and scoreboard queue intact, does not assert port
invariance during the pulse, and adds no unmodelled pulses to asynchronous-reset
contracts. These scheduling changes caught `history_on_invalid`,
`async_history_reset` and `async_valid_reset` without changing the signed-only
110 payload/expectation arrays.
([Driver patch](../evidence/2026-10-26/fir4-driver-comparison-01/stage-review/tbgen.patch))

## Check the test driver, too

Five executable controls covered zero-latency forwarding, busy sequential
operation, prolonged input blocking, renamed active-low synchronous reset and
asynchronous reset. All five passed their required coverage. The blocking
control held an offer for 16 cycles without producer errors; deliberately
breaking the hold logic produced nine monitor errors. This bad-driver probe
was separate from the 27 RTL faults.
([Control and probe evidence](../evidence/2026-10-26/fir4-driver-comparison-01/comparison/result.json))

The comparison retained input/source digests, raw assertion logs and actual
zero `xvlog`, `xelab` and `xsim` process exits. Oracle, reference and fault RTL
were frozen; the original design run and its budgets were preserved. No model
or synthesis calls were needed. The changed runtime subsequently passed
[1,450 software tests](../evidence/2026-10-26/fir4-coverage-tests-01/README.md).

## What remains outside the generic contract

The five misses were `stale_history_reset`, `retained_stage1_reset`,
`retained_stage2_reset`, `retained_stage3_reset` and `combinational_reset_gate`.
They require occupied-reset flush/retain rules or the FIR-specific requirement
that `out_valid` remain observable while synchronous reset is asserted.
The generic reset schema does not express those policies. Inventing them would
reject legitimate designs, so the independent contract checker remains necessary.

The result measures sensitivity to these selected faults. It does not establish
formal equivalence, general reset coverage, FPGA performance gains or improved
LLM generation success. The engineering contribution is an auditable correction
to the verifier, with its remaining coverage boundary documented.
