# fir8 exploration 02: timing progress on the 150 MHz FIR

Exploratory, not a curriculum verdict: `tools/explore.py --tier 2 --entries fir8
--jobs 1 --model gpt-6-luna`, optimize mode, without writing the curriculum
history. Code: main checkout at 05f7ee51 (post-hold merged with the open-items
batch: timing progress, maximize_freq on register-to-register slack).
Exploration 01 is in `explore-tier2-01`.

| Iteration | Verdict | LUT | FF | DSP | WNS ns | reg2reg WNS ns |
|---:|---|---:|---:|---:|---:|---:|
| 0 | seed | 101 | 192 | 6 | -9.918 | -9.918 |
| 1 | ACCEPT (timing_progress) | 131 | 224 | 6 | -2.950 | -2.950 |
| 2 | ACCEPT (timing_progress) | 155 | 214 | 2 | **-2.766** | **-1.989** |
| 3-5 | REJECT before any tool | — | — | — | — | — |

## What the roles showed

- **Timing progress is retained now.** In exploration 01 every candidate was
  discarded because none closed timing, so each iteration restarted from the
  seed. Here two strictly better infeasible designs were kept and built on
  (taxonomy `infeasible_progress_discarded`), cutting the deficit by 72%.
  Timing at 150 MHz is still not closed.
- **The parser blocked a real fix.** Iterations 3-5 all proposed
  `(* IOB = "TRUE" *)` on the registered output, which packs it into the I/O
  block against pad-dominated timing. The interface parser refused attributes
  on port declarations (taxonomy `port_attribute_rejected`, fixed).
- **The planner did not learn from it.** The progress file it reads said only
  "no candidate survived the ladder", so it repeated the same proposal three
  times (taxonomy `rejection_reason_hidden_from_planner`; the progress entry
  now carries each candidate's reason).
