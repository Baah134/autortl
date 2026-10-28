# Harness-generated signed FIR on the Basys 3, run 01

The signed FIR that AutoRTL optimized from 78 to 52 LUTs now runs on a
physical Basys 3, and 100,000 hardware outputs matched an independent Python
model exactly.

- **Design under test:** `hardware/basys3/fir4_on_board/dut/signed_fir4.v`,
  byte-identical to the harness winner
  [`signed_fir4_best.v`](../../2026-10-26/generated-signed-fir4-attempt-01/run/signed_fir4_best.v)
  (SHA-256 `55e3c7d0…37b4ba62`). That file is the run's `best_sha256`, the
  source of its 52-LUT measurement and the file its independent 800-cycle
  verification used. It was not edited.
- **Shell (hand-written):** `rtl/basys3_fir4_shell.v` connects the UART to an
  input FIFO, the FIR, an output FIFO and a 2-byte serializer. A UART break
  restarts the filter.
- **Filter:** y = 3x[n] − 5x[n−1] + 7x[n−2] − 2x[n−3], with signed 8-bit input
  and 13-bit output.
- Vivado 2025.2, `xc7a35tcpg236-1`, 100 MHz; Basys 3 JTAG `210183B31D15A`,
  UART COM10. `manifest.json` binds every source, every file here and the
  bitstream.

## Simulation

| Run | Result |
|---|---|
| `sim/`: the harness winner, 256 samples in chunks of 16, signed extremes first, restart mid-stream | `PASS`: 256/256 matched the testbench model |
| `fault_coef7to6/`: tap 2 coefficient changed from 7 to 6 | `FAIL` as required: 251 of 256 wrong |
| `fault_no_history1_reset/`: reset does not clear the newest history register | `FAIL` as required: 6 errors, including after the mid-stream restart |

## Implementation (`implementation/`)

0 warnings in every phase; WNS +2.718 ns, WHS +0.113 ns. The system uses
160 LUTs and 195 FFs, and the FIR instance uses 49 LUTs, 67 FFs and no DSPs.
That 49 is not comparable to the harness's standalone 52: here Vivado
optimizes the FIR together with its surroundings. The I/O ports are
false-path constrained, so the slack covers internal paths only.

## Hardware (`hardware/`)

| Run | Result |
|---|---|
| `fir_100000.txt`: 100,000 random samples, chunks of 32, restart every 25,000 | `PASS`: 100,000/100,000 matched, 4 restarts, about 1,990 samples/s |
| `fir_wrong_model_5000.txt`: model with 6 instead of 7 | `FAIL` as required: 4,965 of 5,000 differ |
| `fir_recovery_10000.txt`: 10,000 samples, restart every 1,000 | `PASS`: 10,000/10,000 matched, 10 restarts |
| `fir_smoke_2000.txt`: first smoke run, chunks of 16 | `PASS` |

Each run starts with the signed extremes, so the largest expected output,
|y| = 2,169, is the filter's true worst case and fits 13 bits.

Limits: one board and one session. Throughput is limited by the PC's
chunk-and-wait protocol (the output is two bytes per sample), not by the
filter. This exercises the FIR's valid/ready handshake only with the
backpressure that the shell's FIFOs produce. The full contract's handshake
and reset properties are covered by the independent testbench in the
original run's evidence.
