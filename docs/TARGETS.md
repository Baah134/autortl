# Hardware targets and verification scope

## Current reference benchmark

| Setting | Value |
|---|---|
| FPGA part | `xc7a35tcpg236-1`, Artix-7, speed grade -1 |
| Reference clock | 100 MHz, 10 ns period, single `clk` |
| Tools used for recorded results | Vivado 2025.2 |
| External timing assumptions | Explicit ideal zero input/output minimum and maximum delays |
| Board integration in the harness | No board-specific pin or external-interface profile selected |
| Current physical evidence | Synthesis, placement/routing and timing under the recorded constraints, plus the post-hoc Basys 3 hardware validation below |

The part matches the FPGA on the [Digilent Basys 3](https://digilent.com/shop/basys-3-amd-artix-7-fpga-trainer-board-recommended-for-introductory-users/).
Wide arithmetic/streaming ports are IP interfaces; physical deployment also
needs an appropriate board wrapper, communication interface and I/O assignments.

## Basys 3 hardware validation (outside the harness)

Since October 28, 2026, each archived harness winner has also been run on a
physical Basys 3. This is done by `hardware/basys3/harness_winners`, a
hand-written UART shell with real Digilent pin assignments. Every design was
built, programmed and checked on 50,000 transactions against an independent
model; see `evidence/2026-10-28/basys3-harness-winners-01`.

What this establishes, and what it does not:

- It shows that the winners, unedited, operate correctly on hardware through
  their valid/ready interfaces, under randomized backpressure.
- The harness still optimizes against the ideal-I/O benchmark profile above.
  The board shell is a downstream replay of its outputs, not a board profile
  that the harness targets.
- The shell's UART and LED I/O are slow and false-path constrained (inputs
  are synchronized), so its timing reports cover internal paths only. No
  external-interface timing is validated.
- One board revision, one session and room temperature; no soak or
  environmental testing.

Harness-generated board integration remains the future work described in the
requirements section below.

Part and frequency are already configurable on new runs through `--target-part`
and `--target-freq-mhz`. Users need the selected device installed/supported by
their Vivado installation. These options do not install a board profile or
automatically supply realistic external timing. Changing the device or clock
creates a different experiment; keep its measurements separate.

## Package I/O feasibility

The reference part has **106 bonded IOBs** in the retained
[FIR routed utilization report](../evidence/2026-10-26/generated-signed-fir4-attempt-01/run/iter_003/cand_standard/utilization_routed.rpt).
The FIR uses 27. This fully implemented benchmark maps external core ports to
package I/O resources, so count the complete top-level interface before freezing
its contract. This is a planning check, not an automated pin-allocation feature.

A parallel signed8 4x4 matrix/vector interface would need 238 external bits and
cannot fit this package as proposed. Serialization, a board wrapper, another
part or a separately validated core-only flow would change the experiment and
needs an explicit interface/target plan. A count within106 is only a necessary
condition: bank/voltage, clock-capable pins, board connections and timing still
require their own checks. Do not silently relax a contract to force placement.

## Meaning of a timing pass

Setup/hold gates use the retained routed reports and exact constraint/script
identities. A result passing at 100 MHz under ideal I/O assumptions is evidence
for that profile. It does not establish the design's maximum frequency, a real
board's interface timing, or successful programming/operation on hardware.

AMD's [input-delay guidance](https://docs.amd.com/r/2025.1-English/ug903-vivado-using-constraints/Input-Delays)
explains how external timing is represented. Board/interface validation must
account for the actual external devices and clock relationships. Frequency,
latency, throughput and reset requirements remain user-owned fixed contracts.
Agents must not relax them or invent false/multicycle paths to obtain a pass.

## Requirements before claiming board validation

- Identify the exact board/revision, FPGA part/package/speed grade and usable
  interfaces. Define the integration wrapper and physical connections.
- Supply reviewed pin assignments, I/O standards/voltage banks, primary and
  generated clocks, external minimum/maximum delays, and applicable uncertainty.
- Declare supported clock domains and reset behavior. Current generated graders
  support the documented single-clock modes; multi-clock/CDC needs its own
  verified implementation and checks.
- Freeze trusted constraint files with source/configuration hashes before
  optimization; preserve their scope and any justified timing exceptions.
- Check constraint coverage and required implementation/design-rule results,
  then perform the defined programming and hardware acceptance procedure.

Validated board profiles and arbitrary trusted board-XDC ingestion are future
work, not capabilities implied by the current frequency/part switches. Do not
substitute benchmark constraints for missing board requirements.

## Software robustness priorities

1. Clear supported interfaces and executable examples for agents and users.
2. Independent, fault-qualified behavioral verification plus physical gates.
3. Fixed budgets, cancellation and recovery with honest accounting and evidence.
4. Preflight dependency/device/tool/login checks and useful failure categories.
5. Reproducible target/tool/source/constraint reports with explicit scope.
6. Repeated matched-task evaluations before broad reliability or superiority
   claims, reporting LUT, DSP, RAM, slice-FF, timing and power tradeoffs together.

Keep the current benchmark as a reproducible reference. Introduce and verify one
complete board profile before advertising broader board support. Add mechanisms
when a concrete requirement or reproduced failure justifies them; retain the
smallest tested implementation.
