# Closing timing on a signed FIR without changing its contract

AutoRTL generated and optimized a four-tap streaming filter from a fixed
specification: **78 → 52 LUTs**, with routed setup slack improving from
**−0.327 → +0.169 ns**. The filter computes
`y[n] = 3x[n] − 5x[n−1] + 7x[n−2] − 2x[n−3]`, using signed 8-bit samples,
13-bit outputs and a three-stage elastic pipeline. History advances only on
accepted input; output must remain stable under backpressure.

The [archived run](../evidence/2026-10-26/generated-signed-fir4-attempt-01/result.json)
used Vivado 2025.2, `xc7a35tcpg236-1` and 100 MHz, with ideal zero minimum/maximum
I/O delays. It consumed 12 model calls within a 16-call ceiling. The actual CLI
model identity was unobserved, so this is an auditable engineering example,
not evidence about a particular model's strength.

## What changed

The [baseline core](../evidence/2026-10-26/generated-signed-fir4-attempt-01/run/modules/signed_fir4_core/signed_fir4_core.v)
propagated readiness through three valid bits. The
[winner](../evidence/2026-10-26/generated-signed-fir4-attempt-01/run/signed_fir4_best.v)
added a register tracking whether all three stages are occupied:

```diff
  wire ready3 = !valid3 || out_ready;
  wire ready2 = !valid2 || ready3;
- wire ready1 = !valid1 || ready2;
- assign in_ready = ready1;
+ assign in_ready = !full || out_ready;
+ // In the clocked block, alongside the valid-register updates:
+ full <= next_valid1 && next_valid2 && next_valid3;
```

Reset clears both occupancy and valids. Updating `full` from the next valid
values preserves `full == (valid1 && valid2 && valid3)` after each edge, rather
than adding a cycle of backpressure delay. The equivalent ready decision now
depends on one registered occupancy bit.

The arithmetic also changed from constant multiplication to explicit signed,
16-bit shift/add expressions: `3x = (x<<<1)+x`, `5h = (h<<<2)+h`,
`7h = (h<<<3)−h` and `2h = h<<<1`. Both versions used zero DSP blocks;
this was a change to logic implementation, not a DSP-to-LUT conversion.

The routed [baseline](../evidence/2026-10-26/generated-signed-fir4-attempt-01/run/iter_000/timing_routed.rpt)
critical path ran from `valid2_reg` to `in_ready` through a LUT4 and output
buffer; the [winner](../evidence/2026-10-26/generated-signed-fir4-attempt-01/run/iter_003/cand_standard/timing_routed.rpt)
used `full_reg`, a LUT2 and output buffer. Both reports show two logic levels;
data-path delay fell 5.653 → 5.156 ns. These reports support the simpler ready-path
explanation. Occupancy and arithmetic changed together, so their individual
contributions to area and timing were not isolated.

| Routed metric | Baseline | Winner |
|---|---:|---:|
| LUTs | 78 | 52 |
| Flip-flops | 66 | 67 |
| Setup / hold slack | −0.327 / +0.029 ns | +0.169 / +0.106 ns |
| DSP / BRAM | 0 / 0 | 0 / 0 |
| Estimated total power | 0.088 W | 0.088 W |

The tradeoff was one extra flip-flop for 26 fewer LUTs and closed timing; no
power reduction was measured.

## Why the result is credible

Before generation, the independent checker passed its correct control and
detected [27 named behavioral faults](../evidence/2026-10-25/signed-fir4-admission-attempt-01/README.md).
The exact saved winner then passed an independent
[800-cycle simulation](../evidence/2026-10-26/generated-signed-fir4-attempt-01/verification/independent/result.json),
including backpressure and resets; compile, elaboration and simulation exits
were retained. The qualification reference was not supplied to generation.

The byte-identical winner subsequently ran inside a handwritten UART/FIFO
shell on a physical Basys 3: [100,000/100,000 outputs matched](../evidence/2026-10-28/basys3-fir4-01/hardware/fir_100000.txt)
an independent Python reference, with four restarts. A wrong-coefficient
[negative control](../evidence/2026-10-28/basys3-fir4-01/hardware/fir_wrong_model_5000.txt)
produced 4,965 mismatches in 5,000 samples. The
[board record](../evidence/2026-10-28/basys3-fir4-01/README.md) binds source and
implementation evidence.

That integrated shell's 160 LUTs and +2.718 ns setup slack describe a different
implementation with false-path-constrained I/O, not the standalone 52-LUT
measurement. This case is FIR4 at 100 MHz; FIR16's separate 150 MHz out-of-context
result is not used here. Finite tests and one board session do not establish
formal equivalence, maximum throughput or universal optimization gains.
