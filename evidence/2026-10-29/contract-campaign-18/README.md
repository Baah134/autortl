# Tier0 campaign18: the model-portability identity, with the model pinned

**2/2 passed, new-cohort streak 1, held false. Model: `gpt-6-luna`, recorded
as requested.**

| Entry | Baseline LUT | Best LUT | FF | Setup ns | Calls | Vivado s |
|---|---:|---:|---:|---:|---:|---:|
| counter | 55 | 53 | 37 | 0.456 | 3 | 496 |
| mux4 | 8 | 8 | 8 | 0.579 | 3 | 515 |

The first gate on the 236-file identity after the merge of
`claude/model-portability` (f7d19e0): tolerant role parsers, a run-pinned
model, planner spec repair, the mechanical seed timescale and the
append-safe curriculum history. Freeze digest `d9e96ea9…`. It ran
`tools/tier0_gate.py --model gpt-6-luna`, so for the first time the cohort
records the model: `runtime_identity.model_identity` is `gpt-6-luna` with
status `requested`, where earlier campaigns record an unobserved CLI
default. Budgets are campaign14's: per entry 1 iteration and 1 candidate,
16 model calls, 20 tool minutes and 30 wall minutes, 1 infrastructure retry.
Vivado 2025.2, xc7a35tcpg236-1, 100 MHz, ideal zero I/O delay.

- The full test receipt passed: 1,516 tests in 496.9 s. The source was
  unchanged before and after.
- Bench exit code 0, 1,100 s wall. Afterwards, the source identity, the
  router-statistics prefix and the curriculum-history prefix were all
  unchanged.
- Both entries passed every mandatory gate. mux4's proposal did not improve
  on its baseline, which tier0 permits.

The Vivado times are about three times campaign17's. The bench ran from
10:46 to 11:04 EDT, and the Windows System log shows the laptop entering
Modern Standby (Reason: Idle Timeout) at 10:46:28, which throttles desktop
processes; other work also shared the machine. Budgets were never
approached and results are unaffected (taxonomy `host_standby_stalls_tools`). `role-report.md` shows
each role's calls and verdicts (tools/role_report.py).

This identity was superseded by the advisory register-to-register timing
change before a hold, so its streak stops at 1.

`run/` holds the bench output, with simulator snapshots and Vivado scratch
folders left out. `archive.py` built this folder, and `archive-manifest.json`
hashes every file.
