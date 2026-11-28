# A UART echo built entirely by the harness, on the Basys 3

Both directions of this echo were written by AutoRTL's agent roles; a person
wrote only the specifications, the independent testbenches and a 3-LUT board
wrapper (reset and LEDs).

```
PC ─115,200 baud─► uart_rx_core ─► rx_fifo ─valid/ready─► byte_fifo ─► uart_tx ─► PC
                   (tier5 uart_rx_fifo_build winner)       (tier3 uart_fifo_build winner)
```

| Path | Built by the roles from | Winner (read unchanged) | Harness result |
|---|---|---|---|
| Receive: 16x oversampling, majority vote, start-bit check, framing-error flag, FIFO, error counters | typed spec (tier 5) | `evidence/2026-10-30/explore-tier5-01/run/uart_rx_fifo_build/uart_rx_fifo_best.v` | missed 100 MHz at baseline; timing recovered, then 70 → 55 LUT |
| Transmit: FIFO + 8N1 transmitter | a prose request (tier 3) | `evidence/2026-11-01/explore-tier3-08/run/uart_fifo_build/iter_004/cand_standard/uart_fifo.v` | missed 100 MHz at baseline; timing recovered, then 170 → 36 LUT |

`winners.sha256` lists each file's raw SHA-256 and its LF-normalized SHA-256;
the receiver equals its run's recorded `best_sha256`, and the transmitter's
normalized hash equals iteration 4's `final_source_sha256` (the run ended on its
tool budget with iteration 4 as the verified best).

## Board parameters

Each winner's mechanical top fixes simulation-sized parameters, so the wrapper
(`hardware/basys3/harness_built/uart_echo_all/board/rtl/basys3_harness_echo.v`)
instantiates the four child modules directly and repeats the tops' wiring with
board values: `OVERSAMPLE_DIV = 54` and `CLKS_PER_BIT = 864`, so 864 clocks per
bit on both sides (115,741 baud, 0.47% faster than the PC, so the transmitter
always keeps up), and the FIFO depths the qualified testbenches exercised
(`ADDR_BITS = 3`, `DEPTH = 8`). Both parameters were verified at other values by
the independent testbenches; the board simulation below covers these values.

## Results

| Check | Result |
|---|---|
| Board simulation (`sim/tb_board_pass.log`): 96 back-to-back bytes at the PC's 868.06-clock bit period, independent receiver at bit centres | **TEST PASSED**, error counters 0 |
| Negative control in simulation: receiver `OVERSAMPLE_DIV` 60 (`sim/wrong_baud_control_wrapper.v`) | TEST FAILED, as required |
| Build (`build/`) | 120 LUT (12 as distributed RAM), 106 FF; WNS +5.656 ns, WHS +0.078 ns at 100 MHz; 0 warnings |
| Hardware, 100,000 bytes in 32-byte chunks | **100,000 / 100,000, 0 missing, 0 mismatches** |
| Hardware, continuous stream at full line rate | **1,000,000 / 1,000,000, 0 missing, 0 mismatches**, 11,536 bytes/s |
| Hardware negative control: PC at 106,000 baud | FAIL, as required; the next run at 115,200 passed |

Before this, the board path was smoke-tested by reprogramming the archived
`sync_fifo` winner bitstream (`basys3-bitstreams-01`): 2,000 / 2,000, 0
mismatches. Programming is volatile (JTAG); the configuration flash was not
touched.

## Reproduce

```
vivado -mode batch -source hardware/basys3/harness_built/uart_echo_all/board/scripts/build.tcl \
    -tclargs <out dir> <receiver winner .v> <transmitter winner .v>
vivado -mode batch -source hardware/basys3/harness_winners/scripts/program.tcl -tclargs <out dir>/basys3_harness_echo.bit
python hardware/basys3/uart_echo/scripts/echo_test.py --port COM10 --mode stream --bytes 1000000
```
