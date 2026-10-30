# Tier0 campaign25: the hardened identity, run 2

**2/2 passed, streak 2, held false. Model: `gpt-6-luna` (requested).**

| Entry | Baseline LUT | Best LUT | FF | Setup ns | Reg-to-reg ns (advisory) | Calls | Tokens in / out |
|---|---:|---:|---:|---:|---:|---:|---:|
| counter | 55 | 53 | 37 | 0.456 | 1.912 | 3 | 113,606 / 2,087 |
| mux4 | 8 | 8 | 8 | 0.579 | none (no register-to-register path) | 3 | 106,267 / 2,016 |

The second consecutive gate on the hardened 272-file identity (0cf7413, the
same freeze as campaign24). `run.py doctor`, then the full test receipt
(1,654 harness tests), then the bench with `--model gpt-6-luna --jobs 2`; the
source, router-statistics and history prefixes were unchanged. The counter
improved 55 → 53 LUTs and was accepted; mux4 kept its baseline, which tier0
permits. No repair calls were needed.

`role-report.md` lists each role's calls, tokens and verdicts. `run/` holds
the bench output without simulator snapshots or Vivado scratch folders;
`archive.py` built this folder and `archive-manifest.json` hashes every file.
