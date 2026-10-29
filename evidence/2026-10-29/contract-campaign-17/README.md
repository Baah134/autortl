# Fresh full tier0 campaign17: tier0 held on the changed harness

**2/2 passed, new-cohort streak 3, held true.**

| Entry | Baseline LUT | Best LUT | FF | Setup ns | Calls | Vivado s |
|---|---:|---:|---:|---:|---:|---:|
| counter | 55 | 53 | 37 | 0.456 | 3 | 161 |
| mux4 | 8 | 8 | 8 | 0.579 | 3 | 162 |

This is the third consecutive qualifying tier0 run on the 232-file identity
that contract-campaign-15 froze after bc959cc and e062271, so the curriculum
runner recorded tier0 as held (`history-at-contract-campaign-17.jsonl`, last
record: `qualified` true, `consecutive_qualifying_runs` 3, `held` true). All
three runs share the cohort `78b298ad…` and the freeze digest `a611829c…`.
It ran with the same `tools/tier0_gate.py`, which is copied here, and the
same budgets: per entry 1 iteration and 1 candidate, 16 model calls, 20 tool
minutes and 30 wall minutes, 1 infrastructure retry. The setup is Vivado
2025.2, xc7a35tcpg236-1, 100 MHz, with ideal zero minimum and maximum I/O
delay.

- The full test receipt passed: 1,461 tests in 299.8 s
  (`contract-campaign-17-tests.json`). The source was unchanged before and
  after.
- Bench exit code 0, 405 s wall. Afterwards, the source identity, the
  router-statistics prefix and the curriculum-history prefix were all
  unchanged (`contract-campaign-17-launch-result.json`).
- Both entries passed the mandatory simulation, tool-exit, routed-metric and
  timing gates. mux4's proposal did not improve on its baseline, which tier0
  permits.

| Run | counter LUT | mux4 LUT | Streak | Held |
|---|---:|---:|---:|---|
| contract-campaign-15 | 55 → 53 | 8 | 1 | false |
| contract-campaign-16 | 55 → 31 | 8 | 2 | false |
| contract-campaign-17 | 55 → 53 | 8 | 3 | true |

This winner kept the dead `prev_count` register and compared `count` against
all ones (`&count`) for overflow, which is why it lands at 53 LUT, like
campaign15, and not at campaign16's 31. The model identity is the unobserved
Codex CLI default.

`run/` holds the bench output, with simulator snapshots and Vivado scratch
folders left out. `archive.py` built this folder, and `archive-manifest.json`
hashes every file.
