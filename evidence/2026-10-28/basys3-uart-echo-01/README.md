# Basys 3 UART echo bring-up 01 (superseded by 02)

First physical-hardware run in this repository, kept as found. The design was
hand-written, not harness output. An independent review then found that this
version cannot sustain a continuous stream, and the run below confirmed it on
the board. The fix and its evidence are in
[basys3-uart-echo-02](../basys3-uart-echo-02/README.md).

- Tools: Vivado 2025.2 batch non-project flow, `xc7a35tcpg236-1`, 100 MHz.
- Board: Digilent Basys 3 over USB; Digilent JTAG target `210183B31D15A`, UART on COM10.
- Sources: `source-snapshot/`, byte-identical to the copy at
  `Downloads/basys3-bringup` that was built and programmed. `manifest.json`
  holds one SHA-256 per file and the programmed bitstream's SHA-256.

| File | Result |
|---|---|
| `xvlog.txt`, `xelab.txt`, `xsim.txt` | 64 bytes at exactly the design's own rate: `PASS` |
| `vivado_build.log`, `timing_summary.rpt`, `utilization.rpt`, `drc.rpt` | 0 warnings; WNS +5.451 ns, WHS +0.081 ns; 82 LUT, 90 FF, 12 IOB |
| `program.log` | Programmed `xc7a35t_0` |
| `echo_test_115200.txt` | Chunked (256 bytes, then wait for the echo): 20,000 bytes, 0 missing, 0 mismatches |
| `echo_test_57600_negative.txt` | Required failure at the wrong baud rate. This old checker printed `sent 2000`, but it wrote only the first 256-byte chunk before stopping |
| `echo_test_115200_recovery.txt` | Chunked: 5,000 bytes, 0 missing, 0 mismatches |
| `echo_stream_100000_unfixed.txt` | **Line-rate stream: FAIL.** First lost byte at index 9,696; 150 of 100,000 missing |

The streaming run used the newer line-rate checker, kept as
`checker/echo_test_stream.py` (SHA-256 `3ff887ff…f5a63`; last edited 17:52:07,
11 seconds before the run). The board still held the version 01 bitstream: it
was programmed at 17:38, the run finished at 17:52, and version 02 was not
programmed until after 18:00.

Why it failed: the transmitter took 10 full bit times plus one idle clock per
byte (8,681 clocks, 115,194 baud), while the PC sent about 0.15% faster. The
16-byte FIFO filled within about a second, then dropped bytes without any
flag. The chunked checker paused after every 256 bytes, so it never exposed
this. The simulation also missed it, because its sender ran at exactly the
design's rate.

The I/O ports are false-path constrained (synchronized inputs, slow outputs),
so the slack covers internal paths only. The bitstream is not committed.
