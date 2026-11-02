# Tier 5 — Hardest build entries

Three `build`-mode entries from typed JSON specs, each with an independent
top-level testbench and qualification material, in the tier4 format:

| Entry | Top | Shape | Generated golden | What it adds over tier 4 |
|---|---|---|---|---|
| `uart_rx_fifo_build` | `uart_rx_fifo` | 3 children, 4 connections, `OVERSAMPLE_DIV`, `ADDR_BITS` | yes (per child, cycle level) | 16x oversampled UART receive (synchronizer, majority vote, false starts, framing errors), FIFO with pop/push when full, saturating counters, parameter-dependent schedules of 150+ cycles per frame |
| `fir16_sym_build` | `fir16_sym` | 1 child, scoreboard, latency 5, 150 MHz | yes | 16-tap symmetric FIR with 17-bit pre-adder, round half up and saturation, five-slot elastic pipeline with exact bubble collapse, DSP/LUT trade |
| `axil_regs_build` | `axil_regs` | 3 children, 5 connections (one 256-bit) | yes (per child, cycle level) | AXI4-Lite slave: independent AW/W/B and AR/R, SLVERR decode, byte strobes, write-1-to-clear, read-only registers, response ordering |

A multi-module build sends every child through the generated golden path, so
the UART and AXI children are cycle-level fixed-latency modules whose outputs
depend only on registered state, with their handshake ports tagged
`protocol: none` (each entry's README explains why). Every spec example holds
single integer inputs constant for `after_cycles` steps from reset, with
`after_cycles` at most 310.

`axil_regs_build` is implemented out of context (`implementation:
out_of_context` in its meta.yaml): an AXI4-Lite slave is an SoC block, and its
169 port bits exceed the 106 user I/O of xc7a35tcpg236-1. The other two entries
(38 and 22 port bits) are chip tops. See that entry's README.

Each entry's `qualification/reference.v` holds the reference children plus the
mechanical top (byte-identical to `top_verilog(spec)`), and
`qualification/mutants.json` holds ten single-site `find`/`replace` faults.
Qualify a testbench with Vivado before trusting it:

```powershell
python curriculum/tier5/qualify_tier5.py curriculum/tier5/<entry> runs/tier5-qual/<entry>
```

`qualify_tier5.py` reuses `curriculum/tier4/qualify_tier4.py` unchanged: the
control must print `TEST PASSED` and every mutant must produce a raw `FAIL` line
and `TEST FAILED` (a watchdog or compile error is not a detection).
`tests/test_tier5_fixtures.py` checks the static invariants only, plus
hand-written test-only oracles that agree with every spec example and fit the
generated testbench path.

None of these testbenches has been simulated. A hand-written Python emulation of
each testbench schedule against the reference and the mutants (kept outside the
repository) agreed with every reference and caught all thirty mutants; that is
reading-level evidence, not compilation, simulation or PPA.

Earlier plans for this tier (pipelined AES round, async FIFO as the CDC exam,
RISC-V ALU/regfile/decode slice, memory arbiter) remain candidates for later
entries.
