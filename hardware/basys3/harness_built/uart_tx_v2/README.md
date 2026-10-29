# UART transmitter v2: a contract revised by a hardware measurement

The v1 contract (`../uart_tx`) asked for a full-length stop bit. On the
board, the harness's v1 transmitter echoed chunked traffic perfectly, but a
continuous line-rate stream lost its first byte at 19,392. Two different
generated implementations failed at the same byte, which pointed at the
contract rather than the code. The PC sends about 0.17% fast, and a frame
that takes 10·DIV (+1) cycles cannot keep up. The board's hand-written v02
echo had already solved the same problem by shortening its stop bit.

So v2 changes the **specification**, not any RTL. The stop bit lasts
`STOP = DIV − DIV/16` cycles, 814 at `DIV=868`. Back-to-back frames repeat
every 9·DIV + STOP + 1 = 8,627 cycles, so the transmitter keeps up with a
sender up to 0.6% fast. Then the harness regenerates the transmitter from
the revised contract.

## What else changed from v1

- **`uart_tx_tb.v` checks the top only.** In v1 the testbench also
  instantiated `uart_tx_core`. That pinned the child, which stopped the
  optimizer from inlining it, and it exposed a harness gap that is now
  fixed (taxonomy `stale_companion_masks_inlined_candidate`). The v2 top is
  the board configuration at `DIV=868`, and the testbench grades exactly
  that. It sends all 256 byte values through complete frames, with random
  gaps, back-to-back frames, noise while busy and three resets in the middle
  of frames. Every edge is checked against a cycle-exact reference.
- **Qualification.** `qualification/qualify_tb.py` passes the hand
  reference and fails all 11 mutants. Two of the mutants target v2
  directly: a full-length stop bit (the v1 behavior) and a stop bit one
  cycle short.

The board shell is unchanged: `../uart_tx/board`, the same receive path,
FIFO and pins.

## Result

The harness went from a 40-LUT baseline to a **24-LUT / 24-FF** winner,
timing met, in 14 model calls and 13.7 minutes. Unedited on the Basys 3, it
**streamed 1,000,000 of 1,000,000 bytes at full line rate with 0 errors.**
The v1 designs lost their first byte after 19,392. It also passed chunked
traffic, the wrong-baud control failed, and a stream after the control
passed
([evidence/2026-10-29/harness-uart-tx-v2-01](../../../../evidence/2026-10-29/harness-uart-tx-v2-01/README.md)).