# Tier0 campaign28: the merged identity, run 1

**2/2 passed, streak 1, held false. Model: `gpt-6-luna` (requested).**

| Entry | Baseline LUT | Best LUT | FF | Setup ns | Reg-to-reg ns (advisory) | Calls | Tokens in / out |
|---|---:|---:|---:|---:|---:|---:|---:|
| counter | 55 | 53 | 37 | 0.456 | 1.912 | 3 | 114,178 / 2,028 |
| mux4 | 8 | 8 | 8 | 0.579 | none (no register-to-register path) | 3 | 107,312 / 2,083 |

The first gate on the 273-file identity ca61dbc: the hardened harness plus the
takeover of Codex's review (golden-sandbox hardening, string-aware RTL safety
gate, host-failure triage, baseline-repair companion gate, proven board
simulation, stale-lock and per-entry model-identity fixes). `run.py doctor`,
then the full test receipt (1,706 harness tests), then the bench with
`--model gpt-6-luna --jobs 2`. A tier2 exploration (`tools/explore.py`, which
never writes the curriculum history) shared the machine; the source,
router-statistics and history prefixes were unchanged.

Counter 55 → 53 LUTs, accepted; mux4 kept its baseline, which tier0 permits.

`role-report.md` lists each role's calls, tokens and verdicts. `run/` holds
the bench output without simulator snapshots or Vivado scratch folders;
`archive.py` built this folder and `archive-manifest.json` hashes every file.
