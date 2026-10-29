# Fresh full tier0 campaign15: the merge gate for the changed harness

**2/2 passed, new-cohort streak 1, held false.**

| Entry | Baseline LUT | Best LUT | FF | Setup ns | Calls | Vivado s |
|---|---:|---:|---:|---:|---:|---:|
| counter | 55 | 53 | 37 | 0.456 | 3 | 187 |
| mux4 | 8 | 8 | 8 | 0.579 | 3 | 168 |

This is the full merge gate on the harness after bc959cc
(`stale_companion_masks_inlined_candidate`) and e062271
(`checkpoint_replace_denied`). It ran at git commit 25549e9 with
`tools/tier0_gate.py`, which is copied here.

campaign14 could not be launched. It asserts the 230-file source freeze that
predates those fixes, so it would have refused, and rightly. This gate
freezes the current 232-file identity instead: the same selection, where
exactly the 9 files of the two fixes differ. It uses campaign14's budgets and
arguments unchanged: per entry 1 iteration and 1 candidate, 16 model calls,
20 tool minutes and 30 wall minutes, 1 infrastructure retry.
The setup is Vivado 2025.2, xc7a35tcpg236-1, 100 MHz, with ideal zero
minimum and maximum I/O delay.

- The full test receipt passed: 1,461 tests in 306.6 s
  (`contract-campaign-15-tests.json`). The source was unchanged before and
  after.
- Bench exit code 0, 445 s wall. Afterwards, the source identity, the
  router-statistics prefix and the curriculum-history prefix were all
  unchanged (`contract-campaign-15-launch-result.json`).
- Both entries passed the mandatory simulation, tool-exit, routed-metric and
  timing gates. mux4's proposal did not improve on its baseline, which tier0
  permits, as in campaign12.

The results match campaign12 on the earlier harness exactly (counter 55 →
53 LUT, mux4 8 LUT). The fixes changed the runtime identity, so earlier
cohort streaks do not carry over. A held tier still needs three consecutive
qualifying runs. The model identity is the unobserved Codex CLI default.

`run/` holds the bench output, with simulator snapshots and Vivado scratch
folders left out. `history-at-contract-campaign-15.jsonl` is the curriculum
history at the end of the gate. `archive.py` built this folder, and
`archive-manifest.json` hashes every file.
