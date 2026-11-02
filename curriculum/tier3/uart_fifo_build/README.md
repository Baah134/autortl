# UART transmitter fed by a FIFO (tier 3, prose build)

`spec.md` is a prose request: the planner writes the typed spec and chooses the
decomposition (at least a synchronous FIFO and `uart_tx`, plus the mechanical
top). What it may not choose is the boundary the trusted testbench connects to.

## Fixed interface

Top `uart_fifo`, no parameters: `clk`, `rst` (synchronous, active high),
`in_data[7:0]`, `in_valid`, `in_ready` (out), `tx` (out, idle high). At the top
one bit lasts CLKS_PER_BIT = 16 clk cycles (160-cycle frame) and the FIFO holds
DEPTH = 8 waiting bytes.

Child `uart_tx #(parameter CLKS_PER_BIT = 16)`: `clk`, `rst`, `tx_data[7:0]`,
`tx_valid`, `tx_ready` (out), `tx` (out). Its name, parameter and ports are
fixed because the mechanical top has no parameter list, so the only way the
testbench can check a non-default bit period is to instantiate the child
directly (the same reason `spi_master_build` instantiates `spi_master_core`).
The FIFO's name and ports other than `in_*`, `clk` and `rst` stay free.

## Contract (cycle exact)

- 8N1, LSB first. A frame starting at edge s drives bit floor(j/P) after edge
  s+j: start 0, data 0..7, stop 1, for j = 0..10P-1.
- `uart_tx.tx_ready` = idle, or the last cycle of the stop bit, so a waiting
  byte starts at s+10P with no idle cycle between frames.
- Top: a byte accepted at edge k into an empty idle design starts at edge k+1;
  bytes leave in acceptance order; `in_ready` = (waiting < 8), where the byte
  being sent is not waiting; a start and an acceptance may share an edge.
- `in_ready`, `tx_ready` and `tx` depend only on registered state.
- Synchronous reset discards waiting bytes and the frame in progress, accepts
  nothing, and leaves `tx` = 1 and `in_ready` = 1. Off-edge pulses do nothing.

These rules make every correct implementation observably identical at the top
ports, which is what lets one independent testbench judge any decomposition.

## Why `generate_golden: false`

As for `spi_master_build`, the independent testbench is the authority for the
serial timing: `tx` must be checked every cycle against a frame schedule, which
no transaction-level oracle expresses. The flag only matters if the planner
returns a single module (trusted-testbench-only path). With the required two or
more children, the harness still generates and qualifies a per-child oracle and
testbench for each child and then verifies the integrated top with this
testbench, which is what the "Multi-module build requires trusted integration
testbench" gate (explore-tier3-07) needs.

## Independent testbench

`uart_fifo_tb.v` runs four concurrent cases: CLKS_PER_BIT 16 through
`uart_fifo`, and 2, 3 and 7 through `uart_tx` directly. Each case keeps its own
model (waiting-byte queue and frame timer), checks `in_ready`/`tx_ready` and
`tx` before and after every rising edge, and runs a UART receiver that samples
`tx` at bit centres and compares each frame with an expected-byte queue
(conservation: accepted = received + flushed by reset). Stimulus: reset with a
byte offered, six directed bytes (0xA5, 0x00, 0xFF, 0x01, 0x80, 0x5A), a
back-to-back burst, fill to full with the source holding `in_valid`, a
synchronous reset at every frame phase 0..10P-1 with bytes waiting or offered,
off-edge reset pulses during frames and idle, and seeded xorshift32 traffic
(dense, sparse, idle and half-rate phases, `in_valid` dropped without transfer)
with one reset. Coverage counters must reach fixed minimums. About 40k cycles
for the top case; the watchdog is 300k cycles.

## Qualification (xsim, Vivado 2025.2)

`qualification/reference.v` holds the reference children (`sync_fifo`,
`uart_tx`) plus the top, byte-identical to `top_verilog()` of
`qualification/reference_spec.json` (the reference decomposition, not the
entry spec). `qualification/qualification.json` and `console.txt` are the
recorded run of

```powershell
python curriculum/tier4/qualify_tier4.py curriculum/tier3/uart_fifo_build runs/uart-fifo-qual
```

| Case | Verdict | Cases that failed |
|---|---|---|
| reference | TEST PASSED | none |
| msb_first | TEST FAILED: 40671 errors | all four |
| stop_bit_low | TEST FAILED: 13912 errors | all four |
| bit_period_one_long | TEST FAILED: 65384 errors | all four |
| parameter_ignored | TEST FAILED: 23702 errors | CPB 2, 3, 7 only (by design) |
| idle_cycle_between_frames | TEST FAILED: 33208 errors | all four |
| full_one_early | TEST FAILED: 17600 errors | top |
| push_ignores_full | TEST FAILED: 58266 errors | top |
| pop_ignores_tx_ready | TEST FAILED: 88795 errors | top |
| reset_keeps_waiting_bytes | TEST FAILED: 124167 errors | top |
| asynchronous_reset | TEST FAILED: 1288 errors | all four |

Every mutant failed with raw `FAIL BEHAVIOR` lines and no watchdog. This is
testbench admission evidence only; no planner-generated build of this entry
has been run, and nothing here is synthesis, timing or PPA evidence.
`tests/test_tier3_uart_fifo_fixture.py` checks the static invariants and binds
the recorded hashes to the current testbench and mutant sources.
