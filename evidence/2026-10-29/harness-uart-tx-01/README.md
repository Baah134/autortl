# Harness-built UART transmitter, verified and running on the Basys 3

**The harness generated and optimized a UART transmitter from a typed
specification. The same file, unedited, drives the Basys 3's USB-UART TX pin
and echoed 100,000 of 100,000 bytes from the PC with 0 errors.** No
human-written RTL is in the transmit path. A person wrote the contract, the
independent testbenches and the board receive path. The harness's planner,
generator, evaluator and timing-doctor roles, through Codex CLI, wrote the
transmitter.

## What was asked

`hardware/basys3/harness_built/uart_tx/design_spec.json` defines
`uart_tx_core`: UART 8N1 with a valid/ready byte input and parameter
`DIV=868` (115200 baud from 100 MHz). Its frame timing is cycle-exact, and
the mechanical top is `uart_tx`. The run used:

```
python run.py build --spec .../design_spec.json --tb .../uart_tx_tb.v --top uart_tx --generate-golden
  --objective minimize_luts --iterations 3 --best-of-n 2 --max-llm-calls 60
  --max-vivado-minutes 90 --max-wall-minutes 180
```

The part was xc7a35tcpg236-1 at 100 MHz, with the harness's zero-delay I/O
constraints.

## The three runs, failures included

| Run | Outcome | Why |
|---|---|---|
| `run-01-tools-not-on-path` | `build_blocked` | Vivado's `xvlog` was not on PATH in this shell. The harness classified it as infrastructure and retried. It changed no design and stopped. |
| `run-02-crash-then-budget` | crashed, resumed, then `module_failed` | A `tail -F` of `events.jsonl`, used to watch progress, held the file open. On Windows that made the harness's atomic replace fail with `WinError 5`, and the run crashed. `run.py resume` continued from the journal. Then the generated golden model hit its sandbox instruction budget of 200,000 trace events on a 7,813-cycle specification example. The spec was changed to keep its examples under 2,000 cycles. |
| `run-03-done` | `done`, timing met | It took 14 model calls, 365 Vivado-seconds and 9.4 minutes. |

Run 03 started from a baseline of **34 LUTs and 27 FFs**. Iteration 1 was
the best: **22 LUTs and 24 FFs** (−35% LUTs), with setup +0.690 ns and hold
+0.149 ns. Iterations 2 (24 LUTs) and 3 (23 LUTs) were rejected. In its
first check, the harness's own generated testbench missed the
`flip < to >` mutant, and the independent testbench caught it.

## Verification that does not trust the harness

1. **`uart_tx_tb.v`**, the independent integration testbench the harness ran
   as a gate. Before it graded anything, it passed a hand reference and
   failed all 12 mutants (`checks/qualification-uart_tx_tb`).
2. **A gap, found after the run.** The winner flattened away `uart_tx_core`
   and hard-codes 868 cycles per bit. That is the planner's iteration 1
   decision in `run-03-done/progress.md`. The harness still compiled the
   baseline child file beside the winner, so the testbench's `DIV=3`
   instance of `uart_tx_core` tested the baseline core, not the winner. Only
   the `DIV=868` half, 8 frames, exercised the winner. The spec's
   `DIV` range (2..4096) therefore holds for the baseline core only. The
   board uses `DIV=868`, the winner's value.
3. **`verify_winner_tb.v`, written to close that gap.** It instantiates only
   the top `uart_tx` and sends all 256 byte values through complete frames at
   `DIV=868`, with random gaps, input noise while busy, and three resets
   mid-frame. It checks every edge against the same cycle-exact reference.
   It was qualified first: the reference passes, and 11 of 12 mutants fail
   (`checks/qualification-verify_winner_tb`). The 12th,
   `parameter_ignored`, cannot differ at `DIV=868` and is listed as exempt.
   On the winner alone it passed: 256 frames, 188 back-to-back, 3 aborted
   by reset, 2,239,948 cycles (`checks/verify-winner-only`).
4. **Board simulation** (`board/sim/tb_board.v`). A PC model sends 0.2% fast
   and an independent decoder reads `RsTx`. With the winner, 40 of 40 bytes
   come back. It also passes with the hand reference, and fails with the
   bit-order mutant (36 errors), as it should (`checks/board-sim-*`).

## On the board

`hardware/basys3/harness_built/uart_tx/board` wraps the winner in the
hand-written receive path already proven on this board: `uart_rx` and
`shell_fifo` with 32 entries. The build has 0 errors, 0 warnings and 0
critical warnings, setup +4.844 ns and hold +0.037 ns. The harness's
transmitter, kept as its own hierarchy, uses 24 LUTs and 24 FFs on the
board, against the 22 / 24 the harness measured standalone.

| Hardware check (COM10, 115200 baud) | Result |
|---|---|
| 100,000 random bytes in chunks of 32 | **PASS: 100,000 / 100,000, 0 missing, 0 mismatches** |
| PC at 110,000 baud (4.5% off) | passes, because UART's mid-bit sampling tolerates it; not a valid negative control |
| PC at 100,000 baud (13% off): negative control | **FAIL as required**, mismatch at byte 2 |
| 20,000 bytes after the controls | PASS: 20,000 / 20,000 |
| Continuous line-rate stream, 30,000 bytes | first loss at byte 19,392 (see below) |

The stream loss follows from the contract, not from a bug. The spec makes
the stop bit a full `DIV` cycles (and back-to-back frames `DIV+1`), while
the PC sends about 0.17% fast. That works out to 14.3 cycles of drift per
frame, so the 32-entry FIFO fills after about 19,400 bytes. That is the same
rate the hand-written v01 echo showed (16 entries, first loss at byte 9,696).
The hand-written v02 fixed it with a shortened stop bit. The equivalent
change here would go in the specification, followed by another harness run.
Chunked traffic is unaffected.

## Files

- `run-0*`: the three harness run folders and their console output. All of
  `run-03-done` is here: prompts, plans, journal, candidates, reports and
  `uart_tx_best.v`.
- `checks/`: both testbench qualifications, the winner-only verification
  and the three board simulations, with every source and simulator log.
- `board/`: the bitstream, build and timing reports, programming log and
  every hardware result.
- `archive.py` built this folder. It left out simulator snapshots
  (`xsim.dir`, which hold compiled executables) and Vivado scratch folders
  (`.Xil`). `archive-manifest.json` lists the SHA-256 of every file here.
