# The same UART build on the fixed harness, also on the Basys 3

[harness-uart-tx-01](../harness-uart-tx-01/README.md) found a harness
verification gap. The optimizer inlined the frozen child `uart_tx_core`
into the top. The trusted testbench instantiated `uart_tx_core` directly,
so the stale child file kept those checks passing without testing the
winner, and the spec's `DIV` parameter range was silently lost.

Commit bc959cc fixed the harness. The fix was recorded first as taxonomy
`stale_companion_masks_inlined_candidate`. `autortl/companions.py` now
rejects any candidate whose top no longer reaches a companion that the
trusted testbench instantiates, as a design failure inside the bounded
repair loop. The candidate context names those companions under
`must_keep_instantiating`. Nine new tests were added, and all 1,459
regression tests pass.

This run, 04, repeats run 03 exactly (same spec, testbench, budgets and
command) on the fixed harness.

## What changed

| | Run 03 (before the fix) | Run 04 (fixed harness) |
|---|---|---|
| Winner | inlined the core and hard-coded 868 cycles per bit | keeps `uart_tx_core #(.DIV(868))`; the `DIV` parameter survives |
| What the testbench's `DIV=3` half tested | the stale baseline core, not the winner | the winner's own core |
| LUT / FF, harness-measured | 34 → **22** / 24 | 39 / 28 (baseline kept; no candidate improved) |
| Model calls, elapsed | 14, 9.4 min | 16, 9.4 min |

Run 04 found no improvement. With the core pinned by the testbench, the
only editable part is a top that is pure wiring. All three of its plans
say to keep the `uart_tx_core` instance unchanged (`run-04-done/progress.md`),
and all three were rejected for not improving. The fix traded the 35% LUT
reduction for a winner whose parameterization is actually verified. That
was the right trade, because the spec asked for the parameter.

The baselines differ (34 vs 39 LUTs) because the core is generated afresh
each run and model output varies.

The candidate-context text is not written to disk. Recomputing it from run
04's own inputs gives `must_keep_instantiating: ["uart_tx_core"]`, and run
04's recorded runtime identity includes `autortl/companions.py` at the fixed
version. Run 03's identity does not include that file.

## Verification and board results

The same independent checks as run 01 were run on the winner and its core:

| Check | Result |
|---|---|
| `uart_tx_tb.v` (both halves now test the winner) | PASS: DIV=868 8 frames, DIV=3 2,513 frames |
| `verify_winner_tb.v` (all 256 values, 2.24M cycles) | PASS: 256 frames, 188 back-to-back, 3 reset-aborted |
| Board simulation, PC 0.2% fast | PASS: 40 / 40 |
| Board build | 0 warnings; setup +4.898 ns, hold +0.070 ns; transmitter 38 LUT / 28 FF on the board |
| Hardware: 100,000 bytes in chunks of 32 | **PASS: 100,000 / 100,000, 0 errors** |
| Hardware: PC at 100,000 baud (control) | FAIL as required, at byte 2 |
| Hardware: 20,000 bytes afterwards | PASS |
| Hardware: line-rate stream | first loss at byte 19,392, the same byte as run 03 |

Two different generated implementations lose the stream at the identical
byte. That confirms the loss is set by the contract (a full-length stop bit)
and the PC's clock, not by either implementation.

`archive.py` built this folder. As in run 01, it left out simulator
snapshots and Vivado scratch folders, and `archive-manifest.json` hashes
every file.
