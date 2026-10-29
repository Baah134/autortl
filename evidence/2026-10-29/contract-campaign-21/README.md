# Tier0 campaign21: the final identity, run 2

**2/2 passed, streak 2, held false. Model: `gpt-6-luna` (requested).**

| Entry | Baseline LUT | Best LUT | FF | Setup ns | Reg-to-reg ns (advisory) | Calls | Tokens in / out |
|---|---:|---:|---:|---:|---:|---:|---:|
| counter | 55 | 53 | 37 | 0.456 | 1.912 | 3 | 115,001 / 1,689 |
| mux4 | 8 | 8 | 8 | 0.579 | none (no register-to-register path) | 3 | 107,717 / 2,360 |

The second consecutive gate on the 249-file identity (7c592d6, freeze
`022ab35a…`, the same as campaign20), run with
`tools/tier0_gate.py --model gpt-6-luna --jobs 2` and campaign14's budgets.
The full test receipt passed; bench 386 s with both entries in parallel; the
source, router-statistics and history prefixes were unchanged.

The counter improved 55 → 53 LUTs and the evaluator accepted it, with every
criterion passing; mux4 kept its 8-LUT baseline, which tier0 permits. No
repair calls were needed. `role-report.md` lists each role's calls, tokens
and verdicts.

`run/` holds the bench output without simulator snapshots or Vivado scratch
folders; `archive.py` built this folder and `archive-manifest.json` hashes
every file.
