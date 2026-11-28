# Tier6 cordic_build: CORDIC sin/cos built and timing closed

Exploratory, not a curriculum verdict: `tools/explore.py --tier 6 --entries
cordic_build --name explore-tier6-09 --jobs 1 --model gpt-6-luna` on the main
checkout at 4c50e34d. The design: a 16-iteration CORDIC with a combinational
quadrant fold, a combinational arctangent table, an iterative engine and a
combinational output rounding stage, a chip top at 100 MHz. Every accepted
step passed the independent testbench (bit-exact against an integer model of
the contract, within 4 LSB of true sin/cos, qualified in xsim against ten
faults).

| Iteration | Verdict | LUT | FF | WNS ns | WHS ns |
|---:|---|---:|---:|---:|---:|
| 0 | built from the typed spec | 155 | 62 | -1.757 | +0.086 |
| 1 | **timing recovery (final)** | **194** | 95 | **+0.076** | +0.096 |
| 2-4 | REJECT (not smaller) | 194-197 | 95 | met | |

Status `done`, 22 model calls.

## How the harness got here

The baseline met timing internally (register-to-register +0.585 ns); its worst
path ran from the engine register through the output rounding adder to the
`sin_out` pin. Two harness gaps kept the roles from fixing it:

- `critical_path_hidden_from_planner`: the planner never saw the path and
  rewrote the adder's form three times (explore-tier6-03). The advisory
  evidence now names the worst path and its port endpoints, and the timing
  doctor has a port-path category.
- `met_hold_counted_as_regression`: with the path visible the planner
  registered the rounded outputs (-1.757 -> -0.279 ns), but hold slack fell
  from +0.086 to +0.020 ns, past the progress tolerance, so it was discarded
  although hold still passed (explore-tier6-07). Fixed; on this run the same
  move closed timing in one iteration.

Role report: `role-report.md`.
