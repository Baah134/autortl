# Tier0 campaign24: the hardened identity, run 1

**2/2 passed, streak 1, held false. Model: `gpt-6-luna` (requested).**

| Entry | Baseline LUT | Best LUT | FF | Setup ns | Reg-to-reg ns (advisory) | Calls | Tokens in / out |
|---|---:|---:|---:|---:|---:|---:|---:|
| counter | 55 | 53 | 37 | 0.456 | 1.912 | 3 | 114,518 / 1,877 |
| mux4 | 8 | 8 | 8 | 0.579 | none (no register-to-register path) | 3 | 106,775 / 2,625 |

The first gate on the hardened 272-file identity (0cf7413): the RTL safety
gate, the triage fix and the rest of the whole-harness review's fixes, the
golden-sandbox hardening, the tier4 curriculum, the planner example budget
and Verilog-2001 rule, and the backend fixes. The gate ran `run.py doctor`
before anything else, then the full test receipt (1,654 harness tests), then
the bench with `--model gpt-6-luna --jobs 2`. Bench 515 s; the source,
router-statistics and history prefixes were unchanged.

The counter improved 55 → 53 LUTs and the evaluator accepted it; mux4 kept its
8-LUT baseline, which tier0 permits. Both candidates passed the new RTL safety
gate. No repair calls were needed.

`role-report.md` lists each role's calls, tokens and verdicts. `run/` holds
the bench output without simulator snapshots or Vivado scratch folders;
`archive.py` built this folder and `archive-manifest.json` hashes every file.
