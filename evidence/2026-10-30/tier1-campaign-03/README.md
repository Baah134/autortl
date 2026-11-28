# Tier1 campaign03: 4/4, the first qualifying tier1 run

**4/4 passed, streak 1, held false. Model: `gpt-6-luna` (requested).**

| Entry | Mode | Baseline LUT | Best LUT | Setup ns | Calls | Notes |
|---|---|---:|---:|---:|---:|---|
| counter8_build | build | 6 | 6 | 0.424 | 4 | no gain, rejected as written |
| debouncer_build | build from prose | 6 | **3** | 0.731 | 15 | planner wrote the spec in one call; −50% |
| encoder8_build | build | 6 | **3** | 0.591 | 4 | −50% |
| pwm | optimize | 7 | 7 | 0.553 | 15 | no gain; the seed timescale is now mechanical |

The first tier1 gate on the 273-file identity ca61dbc, which also holds tier0
(campaigns 28-30). `run.py doctor`, the full test receipt (1,706 harness
tests), then the bench with `--tier 1 --model gpt-6-luna --jobs 4` (four
entries in parallel, 19.5 minutes); the source, router-statistics and history
prefixes were unchanged.

The debouncer is the entry that ended at spec lint in tier1-campaign-01 (the
planner named the top after its only module) and was blocked by host standby
in tier1-campaign-02. With the structural rules in the spec prompt the
planner's spec passed on its first call, the golden model and generated
testbench qualified, and the optimizer halved the design.

`role-report.md` lists each role's calls, tokens, verdicts and repairs. `run/`
holds the bench output without simulator snapshots or Vivado scratch folders;
`archive.py` built this folder and `archive-manifest.json` hashes every file.
