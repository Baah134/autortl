# Tier2 exploration 01: the first run of every tier2 entry

Exploratory, not a curriculum verdict: `tools/explore.py --tier 2 --jobs 2
--model gpt-6-luna` ran each entry directly through `run.py`, alongside the
tier0 gates, without writing the curriculum history. Identity ca61dbc (the one
that holds tier0, campaigns 28-30). Budgets per entry: iterations from
meta.yaml, best-of-1, 30 model calls, 40 tool and 60 wall minutes.

| Entry | Mode | Result | Baseline (generated or seed) | Best | Calls |
|---|---|---|---|---|---:|
| skid_buffer_build | build | timing recovery, smaller | 14 LUT, WNS -0.132 ns | **12 LUT, WNS +0.036 ns** | 8 |
| sync_fifo_build | build | timing recovery | 13 LUT, WNS -0.931 ns | 21 LUT, WNS +0.063 ns | 8 |
| packet_fifo_build | build | timing recovery | 15 LUT, WNS -1.031 ns | 23 LUT, WNS +0.069 ns | 13 |
| fir8 | optimize | budget exhausted, timing not closed | 101 LUT + 6 DSP, WNS -9.918 ns | not retained (best candidate WNS -2.766 ns) | 21 |

## What the roles showed

- **Build mode works on tier2.** For all three FIFO-style builds the generated
  baseline missed 100 MHz, and the roles recovered timing; the skid buffer
  also got smaller. The recoveries trade area for slack, which the harness
  accepts only when the incumbent is timing-infeasible.
- **fir8 exposed a selection gap.** The seed fails timing by almost 10 ns. The
  roles cut the deficit by 72% (to -2.766 ns, and one candidate moved all
  arithmetic into 4 DSP slices with 0 LUTs), but every candidate was rejected
  because none closed timing, so the incumbent stayed at the seed and each
  iteration restarted from it until the budget ran out. Recorded as
  `infeasible_progress_discarded`; the fix (retain strictly better slack among
  timing-infeasible designs, feasibility still first) is being built on a
  branch.

`role-report-<entry>.md` summarizes each role's calls, tokens, verdicts and
repairs; `python tools/run_view.py run` renders the whole exploration as one
page. `archive-manifest.json` hashes every file.
