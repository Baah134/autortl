# A UART transmitter built by the harness, on the Basys 3

This is the first design that went from a specification to the board with
no human-written RTL in its path. A person wrote the contract
(`design_spec.json`) and an independent testbench. The harness's agent
roles, through Codex, produced the transmitter. Its Verilog runs on the
Basys 3 unedited: it is the logic driving the USB-UART TX pin.

## The contract

`design_spec.json` defines `uart_tx_core`, a UART 8N1 transmitter with a
valid/ready byte input. `DIV=868` cycles per bit gives 115200 baud from
100 MHz, and `DIV` must work across 2..4096, not only at its default. The
contract is cycle-exact:

- A byte is accepted at edge k when `in_valid && in_ready`.
- Bit i of {start, data LSB first, stop} appears on `tx` after edge
  k+i·DIV.
- `in_ready` is low for the whole frame and returns after edge k+10·DIV.
- Outputs are registered, and a synchronous reset aborts a frame.

## Verification that does not trust the harness

`uart_tx_tb.v` is written from the spec alone. It runs the shipped top at
`DIV=868`, the exact board timing, and the core at `DIV=3`, for thousands
of random frames. A cycle-exact reference checks `tx` and `in_ready` after
every edge and before the next. Coverage gates require:

- full frames, including back-to-back frames
- resets in the middle of a frame
- input noise while busy
- every data bit at both levels

Before it graded anything, the testbench was qualified with
`qualification/qualify_tb.py`. It passed a hand-written reference and
failed all 12 mutants in `qualification/mutants.json`: wrong bit order,
bit length off by one either way, missing stop bit, inverted start bit, live
instead of captured data, reset ignored while busy, accepting without
`in_valid`, the parameter ignored, `in_ready` stuck high, `tx` idling low
after reset, and a frame one bit short.

The reference exists only for that qualification. It is not used on the
board.

## On the board

`board/` wraps the harness's top in the hand-written receive path already
proven on this board: `uart_rx` from `hardware/basys3/uart_echo` and
`shell_fifo`. The PC's bytes come back through the harness's transmitter.
`board/sim/tb_board.v` checks that end to end, with a PC model sending
0.2% fast. With the hand reference standing in for the transmitter it
passes 40 of 40 bytes, and with the bit-order mutant it fails, as it should.

## Result

The harness run finished `done`. It went from a 34-LUT / 27-FF baseline to
a **22-LUT / 24-FF** winner with timing met, in 14 model calls and 9.4
minutes. Built for the board, the winner closes with 0 warnings. On the
Basys 3 it **echoed 100,000 of 100,000 bytes with 0 errors**, and a
wrong-baud control failed as required.

The winner flattened away `uart_tx_core` and hard-codes `DIV=868`.
`verify_winner_tb.v` was added to check that exact file at board timing:
all 256 byte values, resets in the middle of frames, and 2.24 million
cycles. It found nothing wrong. The full account is in
[evidence/2026-10-29/harness-uart-tx-01](../../../../evidence/2026-10-29/harness-uart-tx-01/README.md),
which covers the two failed runs, the verification gap the flattening
exposed, and why a continuous stream eventually overflows.

## Reproducing

```
python run.py build --spec hardware/basys3/harness_built/uart_tx/design_spec.json \
    --tb hardware/basys3/harness_built/uart_tx/uart_tx_tb.v --top uart_tx --generate-golden \
    --objective minimize_luts --iterations 3 --best-of-n 2 --max-llm-calls 60 \
    --max-vivado-minutes 90 --max-wall-minutes 180 --output-dir logs/<new run>
python hardware/basys3/harness_built/uart_tx/qualification/qualify_tb.py <out>    # testbench qualification
vivado -mode batch -source hardware/basys3/harness_built/uart_tx/board/scripts/build.tcl \
    -tclargs <winner .v> <out dir>
python hardware/basys3/uart_echo/scripts/echo_test.py --mode chunked --chunk 32 --bytes 100000
```

Model output varies between runs, so a rerun can produce a different winner.
