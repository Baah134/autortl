# An echo whose receiver and transmitter were both built by the harness

`board/` wraps two harness winners, read unchanged from their evidence
folders, in a 3-LUT wrapper that only generates reset and drives LEDs:

- the receive path from the tier 5 `uart_rx_fifo_build` run (typed spec), and
- the transmit path from the tier 3 `uart_fifo_build` run (prose request).

On the Basys 3 it echoed 1,000,000 of 1,000,000 bytes as a continuous
stream at full line rate with 0 errors. The full record, including the
parameter choice, simulation, negative controls and hashes, is in
[evidence/2026-11-01/basys3-harness-echo-01](../../../../evidence/2026-11-01/basys3-harness-echo-01/README.md).

| File | Purpose |
|---|---|
| `board/rtl/basys3_harness_echo.v` | Wrapper: reset, the winners' children with board parameters, LEDs |
| `board/constraints/basys3_harness_echo.xdc` | Pins from Digilent's Basys-3-Master.xdc |
| `board/scripts/build.tcl` | `-tclargs <out dir> <receiver winner .v> <transmitter winner .v>` |
| `board/sim/tb_board.v` | End-to-end check with a PC model at 115,200 baud |

LD0 to LD3 count framing errors and LD4 to LD7 count receive overflows
(both from the harness-built error counters); btnC resets.
