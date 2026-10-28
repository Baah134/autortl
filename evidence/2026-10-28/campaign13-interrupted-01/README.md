# Campaign13 tier0 gate: interrupted, not a result

Campaign13 was the required fresh full tier0 regression for the tested
coverage runtime (230 frozen source files, development commit cbab6cf).
`run_campaign13.py` (copied here) launched it on October 26 at 10:20.

What the saved state shows:

- Only the `counter` entry started. Its last event is iteration 1 synthesis
  `RUNNING` at 10:22:59, with state `GENERATING`. The budget used was 2 model
  calls, 140.8 tool seconds and 168.8 elapsed seconds. `mux4` never started.
- There is no launch-result receipt, completion record or curriculum history
  record. `curriculum/results.jsonl` is still exactly at its prelaunch offset,
  with an unchanged prefix hash.
- `router-records-after-prelaunch.jsonl` holds the 2 router records appended
  after prelaunch, which are this attempt's 2 model calls. The router-stats
  prefix is unchanged.
- No Vivado, xsim or Codex harness worker was running when this was inspected
  on October 28. The interruption's cause is unknown. The previous checkpoint
  recorded a bounded 120-minute keep-awake helper started around 09:41.

Decision (Claude Code, October 28): do not resume this attempt or rerun it
into its directory. The runner refuses an existing output directory by
design, and an interrupted gate cannot count as a pass. The 230 frozen source
identities still match the prelaunch record (0 of 230 changed), so a fresh
gate with the same budgets measures the same runtime. That gate is
campaign14, in its own output and evidence directories.

`run/` holds the text, JSON and RTL from `logs/contract-campaign-13`.
Simulator snapshots and binaries (70 files, about 6 MB) stay only in `logs/`.
This archive is not a tier0 pass and counts toward no held tier.
