# Hardware targets and verification scope

## Current reference benchmark

| Setting | Value |
|---|---|
| FPGA part | `xc7a35tcpg236-1`, Artix-7, speed grade -1 |
| Reference clock | 100 MHz, 10 ns period, single `clk` |
| Tools used for recorded results | Vivado 2025.2 |
| External timing assumptions | Explicit ideal zero input/output minimum and maximum delays |
| Board integration | No board-specific pin or external-interface profile selected |
| Current physical evidence | Synthesis, placement/routing and timing under the recorded constraints |

The part matches the FPGA on the [Digilent Basys 3](https://digilent.com/shop/basys-3-amd-artix-7-fpga-trainer-board-recommended-for-introductory-users/).
That is a device correspondence, not a completed Basys 3 deployment. Wide
arithmetic/streaming ports are IP interfaces; physical deployment also needs an
appropriate board wrapper, communication interface and I/O assignments.

Part and frequency are already configurable on new runs through `--target-part`
and `--target-freq-mhz`. Users need the selected device installed/supported by
their Vivado installation. These options do not install a board profile or
automatically supply realistic external timing. Changing the device or clock
creates a different experiment; keep its measurements separate.

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
