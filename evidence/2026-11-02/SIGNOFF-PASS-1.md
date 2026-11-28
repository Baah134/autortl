# Final sign-off, pass 1 (stopped at tier 2)

`tools/signoff.py --tiers 0 1 2 3 4 5 6 --model gpt-6-luna --date 2026-11-02`
on 3a55327a/67cea45d code (frozen source identity recorded in each campaign's
`*-source-freeze.json`).

| Tier | Campaigns | Result |
|---|---|---|
| 0 | `signoff-t0-01` .. `-03` | 3 consecutive qualifying campaigns: **held** |
| 1 | `signoff-t1-01` .. `-03` | 4/4, 4/4, 4/4: **held** (tier 1's first hold) |
| 2 | `signoff-t2-01` | stopped by hand mid-run; no verdict recorded, not archived |

The pass was stopped at tier 2 because `fir8` (150 MHz, chip top) could never
pass: its best design's worst path was a single register driving the `y_out[26]`
pin, still 2.766 ns over the 6.67 ns period (taxonomy
`chip_top_pad_floor_exceeds_period`), so tier 2 could not reach 80%. The fix
(fir8 out of context, plus larger budgets for uart_fifo and FIR16 so their
runs finish; e30b0ae8) changes the frozen identity, so pass 2 (`signoff2-*`)
re-holds every tier on the final code. These six campaigns remain valid
evidence that tiers 0 and 1 held on the pass-1 identity.
