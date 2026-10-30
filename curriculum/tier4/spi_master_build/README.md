# SPI master, mode 0 (tier 4)

`spi_master` transparently wraps one `spi_master_core #(HALF_PERIOD=2)`.
Ports: `clk`, `rst`, `cmd_data[7:0]`, `cmd_valid`/`cmd_ready`, `rsp_data[7:0]`,
`rsp_valid`/`rsp_ready`, `sclk`, `mosi`, `miso`, `cs_n`. Supported parameter
domain HALF_PERIOD 1..8 (clk cycles per SCLK half period). Latency 33 is the
default minimum accepted-transfer age, 16*HALF_PERIOD+1.

## Contract (cycle exact)

A command accepted at edge k drives `cs_n=0`, `sclk=0`, `mosi=cmd_data[7]` after
k. SCLK toggles at edges k+j*H for j=1..16. Odd j raise SCLK and sample `miso`
(MSB first) at that same clk edge; even j<16 lower SCLK and present the next MOSI
bit. At j=16 the bus returns to idle (`cs_n=1`, `sclk=0`, `mosi=0`) and the
received byte is presented on `rsp_data` with `rsp_valid=1`, held until
`rsp_ready`. `cmd_ready = !busy && !rsp_valid` (registered state only), so one
command is outstanding and the next can be accepted one edge after the response
retires. Synchronous active-high reset aborts any transfer or held response;
off-edge pulses change nothing.

## Why `generate_golden: false`

The harness's generated scoreboard testbench treats each data input as a
transaction payload and changes it after acceptance; MISO is a serial waveform,
and `sclk`/`mosi`/`cs_n` must be checked every cycle, not at response transfer.
No transaction-level Python oracle can express that, so the generated oracle
path does not apply. The build uses the trusted-testbench-only single-module
path (`_generate_verified` against this TB, then the harness's own fault
portfolio). The spec's examples still satisfy `validate_examples` under the
documented transaction convention (MISO held constant, so `rsp_data` is 0x00 or
0xFF and the bus is idle whenever a response is presented).

## What it stresses

- A long multi-cycle schedule (33 to 129 cycles per transfer) that must be exact.
- A public parameter that changes timing but not ports; generated code must not
  hard-code the default (the TB checks HALF_PERIOD 2 via the top, and 1, 3, 8
  via the child directly).
- The MISO sample instant: the TB's slave drives the correct bit only in the
  cycle before each specified sample edge and noise otherwise.
- Single outstanding command, held responses, and reset at every phase.

## Independent testbench

`spi_master_tb.v` runs four concurrent cases (HALF 2 through the mechanical top,
1, 3 and 8 through the child). Each case models the bus schedule exactly, checks
`cmd_ready`, `rsp_valid`, `rsp_data`, `cs_n`, `sclk` and `mosi` before every
rising edge and after its updates, and covers six directed transfers with
response stalls, a command held through a transfer, stall and retirement edge,
a synchronous reset at every transfer phase including the response edge and a
stalled response, off-edge reset pulses during a transfer and a held response,
and seeded random traffic (xorshift32) with one reset. Stimulus follows the
model, never DUT outputs, so stuck or hung DUTs still end with a verdict.

## Qualification (not yet run)

`qualification/reference.v` is the reference child plus the mechanical top;
`qualification/mutants.json` has ten single-site faults. `parameter_ignored` is
caught only by the non-default cases, by design.

```powershell
python curriculum/tier4/qualify_tier4.py curriculum/tier4/spi_master_build runs/tier4-qual/spi_master
```

No simulation of this fixture has been performed; nothing here is evidence of
compilation, mutant detection or PPA.
