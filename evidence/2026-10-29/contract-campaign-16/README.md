# Fresh full tier0 campaign16: the second hold gate on the changed harness

**2/2 passed, new-cohort streak 2, held false.**

| Entry | Baseline LUT | Best LUT | FF | Setup ns | Calls | Vivado s |
|---|---:|---:|---:|---:|---:|---:|
| counter | 55 | 31 | 37 | 0.126 | 3 | 175 |
| mux4 | 8 | 8 | 8 | 0.579 | 3 | 160 |

This is the second consecutive tier0 gate on the 232-file identity that
contract-campaign-15 froze after bc959cc and e062271. The freeze digest
`a611829c…` is identical to campaign15's. It ran with the same
`tools/tier0_gate.py`, which is copied here, and the same budgets: per entry
1 iteration and 1 candidate, 16 model calls, 20 tool minutes and 30 wall
minutes, 1 infrastructure retry. The setup is Vivado 2025.2,
xc7a35tcpg236-1, 100 MHz, with ideal zero minimum and maximum I/O delay.

- The full test receipt passed: 1,461 tests in 306.4 s
  (`contract-campaign-16-tests.json`). The source was unchanged before and
  after.
- Bench exit code 0, 412 s wall. Afterwards, the source identity, the
  router-statistics prefix and the curriculum-history prefix were all
  unchanged (`contract-campaign-16-launch-result.json`).
- Both entries passed the mandatory simulation, tool-exit, routed-metric and
  timing gates. mux4's proposal did not improve on its baseline, which tier0
  permits.

The counter winner (55 → 31 LUT, −44%) is better than campaign15's
(55 → 53). It drops the dead `prev_count` register and takes `overflow` from
the carry-out of one 33-bit increment, instead of comparing `count` against
all ones in a separate 32-bit comparator. Both set overflow exactly when an
enabled increment wraps from all ones, so the contract is unchanged, and the
independent counter testbench passed it. Setup slack fell from 0.494 to
0.126 ns but stays positive. The difference from campaign15 is the model's
proposal, not the harness: the source identity is the same.

`run/` holds the bench output, with simulator snapshots and Vivado scratch
folders left out. `history-at-contract-campaign-16.jsonl` is the curriculum
history at the end of the gate. `archive.py` built this folder, and
`archive-manifest.json` hashes every file.
