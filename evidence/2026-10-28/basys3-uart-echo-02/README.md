# Basys 3 UART echo bring-up 02

Fixed version of [bring-up 01](../basys3-uart-echo-01/README.md), whose echo
lost bytes under a continuous stream. The design is hand-written
`hardware/basys3/uart_echo`, not harness output.

Changes from 01:

- The transmitter's stop bit is 1/16 bit short, so an echoed byte takes 8,627
  clocks including the idle cycle between bytes. That is 0.6% less than the
  8,680.6 clocks of a byte at exactly 115,200 baud. Receivers sample the middle
  of the stop bit, so they still accept it.
- After a frame error, the receiver waits for the line to go high, so a break
  (a line held low) no longer echoes a phantom byte.
- New sticky flags: LD15 lights if the FIFO ever dropped a byte, and LD14 if a
  frame arrived with a low stop bit. Both clear on `btnC`.
- `ASYNC_REG` on both two-flop synchronizers.
- The checker now streams at line rate from a writer thread, and it reports
  the bytes it actually wrote.

Vivado 2025.2, `xc7a35tcpg236-1`, 100 MHz, the Digilent Basys 3 used for run 01
(JTAG `210183B31D15A`, UART COM10). `manifest.json` binds the design and script
SHA-256 values, every file here and the programmed bitstream.

## Simulation (`sim/`, run with `scripts/run_sims.ps1`)

| Scenario | Result |
|---|---|
| Mode 0: 64 bytes at the exact rate, then a start-bit glitch, a low-stop-bit frame, a 12-bit break followed by a good byte, and reset | `PASS` |
| Mode 1: sender 0.5% fast, 1,500 bytes, 2-entry FIFO | `PASS`: 1,500/1,500 in order, no overflow |
| Mode 2: sender 3.1% fast, 800 bytes | `PASS`: overflow flag latched |

Fault checks: each reverts one fix in a copy of the design, and the exact
faulted file is kept next to its outputs.

| Fault | Result |
|---|---|
| `fault_full_stop/`: full-length stop bit | Mode 1 `FAIL` as required, first lost byte at index 381; modes 0 and 2 pass |
| `fault_no_break_wait/`: return to idle right after a frame error | Mode 0 `FAIL` as required (`break produced an echo`); modes 1 and 2 pass |

## Implementation (`implementation/`)

0 warnings in every phase; WNS +4.529 ns, WHS +0.106 ns; 77 LUT, 94 FF,
14 IOB. The I/O ports are false-path constrained (synchronized inputs, slow
outputs), so the slack covers internal paths only.

## Hardware (`hardware/`)

| Run | Result |
|---|---|
| Line-rate stream, 1,000,000 random bytes | `PASS`: 0 missing, 0 mismatches, 11,537 bytes/s over 86.7 s |
| Chunked, 20,000 bytes | `PASS` |
| PC at 57,600 against the 115,200 design | `FAIL` as required: 9,412 of 20,000 missing |
| Line-rate stream, 100,000 bytes after the negative run | `PASS` |

At 115,200 baud 8N1 the nominal line rate is 11,520 bytes/s. The measured
11,537 bytes/s means the PC sends about 0.15% fast, which matches the failure
seen in run 01.

Limits: one board, one session and one PC. No temperature variation, no
`btnC` press during traffic, and LD14/LD15 were not read back by the PC.
