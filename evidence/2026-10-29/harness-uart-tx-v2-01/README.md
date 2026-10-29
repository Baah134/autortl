# v2: a hardware failure drove a spec change, and the harness's new design streams 1,000,000 bytes

**On the Basys 3, the harness's v2 transmitter streamed 1,000,000 of 1,000,000
bytes from the PC at full line rate with 0 errors.** The v1 designs lost a
byte after 19,392 in the same test. Nothing between the two was fixed by
hand in RTL. The fix was a one-line change of meaning in the
specification, and the harness generated a new transmitter from it.

## The loop

1. **v1 on hardware** ([harness-uart-tx-01](../harness-uart-tx-01/README.md),
   [-02](../harness-uart-tx-02/README.md)). Chunked traffic was perfect, but
   a continuous stream lost its first byte at 19,392. Two different
   generated implementations failed at the identical byte, so the cause was
   the contract, not the code. The contract required a full-length stop bit,
   and the PC sends about 0.17% fast.
2. **The spec change** (`hardware/basys3/harness_built/uart_tx_v2/design_spec.json`).
   The stop bit is now `STOP = DIV − DIV/16` = 814 cycles, so back-to-back
   frames take 8,627 cycles instead of 8,681. The transmitter keeps up with a
   sender up to 0.6% fast. It's the same remedy the hand-written v02 echo
   used. The new testbench grades the top only, so the optimizer is free to
   inline. It was qualified first: it passes the hand reference and fails
   all 11 mutants, including the v1 full-length stop bit and a stop bit one
   cycle short.
3. **The harness run** (`run-v2-01-done`). The baseline was 40 LUTs / 28 FFs.
   Iteration 1 reached 26 / 25, iteration 2 was rejected at 28, and
   iteration 3 won with **24 LUTs / 24 FFs** (−40%), setup +0.271 ns and
   hold +0.057 ns. It took 14 model calls, 615 Vivado-seconds and 13.7
   minutes. The winner inlines the core, with `STOP` computed from `DIV`
   as the spec requires.
4. **Independent check** (`checks/winner-only-uart_tx_tb`). The qualified
   testbench, run outside the harness on the winner file alone, passes. It
   covers all 256 byte values through complete frames, 197 back-to-back
   frames and 3 mid-frame resets, over 2,217,293 cycles.
5. **On the board.** The shell is the same as v1 (`../uart_tx/board`). The
   build has 0 warnings, setup +4.913 ns and hold +0.037 ns. The transmitter
   uses 26 LUTs / 24 FFs on the board.

| Hardware check (COM10, 115200 baud) | v1 (runs 03, 04) | v2 |
|---|---|---|
| Continuous line-rate stream | first loss at byte 19,392 | **1,000,000 / 1,000,000, 0 errors, 11,536 bytes/s** |
| 100,000 bytes in chunks of 32 | 100,000 / 100,000 | 100,000 / 100,000 |
| PC at 100,000 baud (control) | fails, as required | fails, as required (byte 1) |
| Stream again after the control | n/a | 100,000 / 100,000 |

11,536 bytes/s is full line rate: 115200 baud at 10 bits per byte is 11,520
bytes/s nominal, and the PC's clock is slightly fast.

## Files

`run-v2-01-done` is the complete harness run: prompts, plans, journal,
candidates, reports and `uart_tx_best.v`, with SHA-256 starting
`9b67f9253b8ada71`. `checks/` holds the testbench qualification and the
winner-only run. `board/` holds the bitstream, reports, programming log and
every hardware result. `archive.py` built the folder, leaving out simulator
snapshots and Vivado scratch folders, and `archive-manifest.json` hashes
every file.
