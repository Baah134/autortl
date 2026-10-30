# UART receiver feeding a FIFO (tier 5)

`uart_rx_fifo` mechanically wires three generated children:

| Child | Parameters | Inputs | Registered outputs |
|---|---|---|---|
| `uart_rx_core` | `OVERSAMPLE_DIV=2` (1..64) | `rx` | `rx_data[7:0]`, `rx_strobe`, `frame_err` (external) |
| `rx_fifo` | `ADDR_BITS=2` (1..4) | `wr_en`, `wr_data` (from the receiver), `out_ready` | `out_data[7:0]`, `out_valid` (external), `overflow` |
| `rx_err_count` | none | `ferr_in`, `ovf_in` | `ferr_count[3:0]`, `ovf_count[3:0]` (external) |

Four explicit connections: `rx_strobe -> wr_en`, `rx_data -> wr_data`,
`frame_err -> ferr_in`, `overflow -> ovf_in`. All children are fixed-latency
1 cycle-level modules with synchronous active-high reset; there is no top
latency annotation.

## Contract (cycle exact)

With D = `OVERSAMPLE_DIV`, a bit lasts 16D cycles. `rx` passes a two-flop
synchronizer that resets to 1, so the line sample at edge i is rx from before
edge i-2. In IDLE the first low sample is the detection edge e0. At frame offset
m = 16D*b + p the receiver votes at p = 7D, 8D, 9D and decides bit b by majority
at p = 9D. A high start bit is a false start (back to IDLE at once). Data is LSB
first. The stop bit is decided at e0 + 153D: high gives a one-cycle `rx_strobe`
with `rx_data`; low gives a one-cycle `frame_err` and waits for the line to go
high (a held break reports one error). The FIFO is first-word-fall-through:
`out_valid = count != 0`, `out_data` is the head byte or 0 when empty, a full
FIFO accepts a write at an edge where it also pops, and a dropped write gives a
one-cycle `overflow`. The counters saturate at 15.

Integrated timing: a good stop decided at edge E is written at E+1 and visible
on `out_valid` after E+1; a framing error decided at E shows on `frame_err` after
E and in `ferr_count` after E+1.

## Why the handshake ports are tagged `protocol: none`

A multi-module build sends every child through the generated golden path, and
`rx_strobe -> wr_en` cannot connect a `valid_ready` port to a plain one. A UART
receiver has no input handshake, so neither child fits the scoreboard shape.
Each child is a cycle-level fixed-latency module whose outputs depend only on
registered state; its generated testbench compares every output every cycle,
which is stricter than a scoreboard. `out_valid`/`out_ready` still follow
valid/ready semantics, and this testbench checks them exactly.

## What it stresses

- Long, parameter-dependent schedules (frames of 153D+1 to 160D cycles). The
  examples use D=2 and stay at or below 310 steps.
- Plausible-but-wrong receivers: a one-flop synchronizer, a single centre
  sample, MSB-first assembly, ignored stop bits, no false-start rejection,
  late votes.
- FIFO corner: a write and a pop at the same edge on a full FIFO.
- Integration: the internal strobe/data/error/overflow wiring is visible only
  through the FIFO port and the counters.

## Independent testbench

`uart_rx_fifo_tb.v` runs three concurrent cases: D=2/A=2 through the mechanical
top, and D=1/A=3 and D=3/A=1 through the children wired by the testbench. Each
case models the synchronized line, frame offsets, votes, FIFO queue and counters,
and checks every output port before and after each rising edge. Stimulus comes
from the model, never from DUT outputs. Coverage: clean frames, back-to-back
frames at the minimum spacing (start right after the stop decision), noisy frames
(random values at every ignored offset and one inverted vote per bit), glitches
with at most one low start vote followed by the earliest legal restart, a start
with two low votes (a real 0xFF frame), framing errors with the earliest restart,
long breaks, fill/overflow and pop-at-write on a full FIFO, synchronous resets
mid-frame and while waiting after a break, off-edge reset pulses, saturation of
both counters, and 36 seeded random events (xorshift32). A frame-expectation
queue self-checks the model (`CHECKER_FAIL`).

## Qualification (not yet run)

`qualification/reference.v` holds the three reference children and the
mechanical top (byte-identical to `top_verilog(spec)`); `qualification/mutants.json`
has ten single-site faults across the receiver, the FIFO, the counters and the
top wiring. `divider_ignored` is caught only by the non-default cases and
`top_overflow_counter_miswired` only by the top case, by design.

```powershell
python curriculum/tier5/qualify_tier5.py curriculum/tier5/uart_rx_fifo_build runs/tier5-qual/uart_rx_fifo
```

No simulation of this fixture has been performed. A hand-written Python
emulation of the testbench schedule, the reference and the mutants (not
committed) agreed with the reference and caught all ten mutants. That is not
evidence of compilation, simulator behavior, mutant detection or PPA.
