# fir8 at 150 MHz out of context: closes

Exploratory, not a curriculum verdict: `tools/explore.py --tier 2 --entries fir8
--jobs 1 --model gpt-6-luna` on e30b0ae8, after fir8's meta moved it out of
context. Sign-off pass 1 had shown that as a chip top fir8 could never pass:
its best design's worst path was a single register driving the `y_out[26]` pin,
still 2.766 ns over the 6.67 ns period (taxonomy
`chip_top_pad_floor_exceeds_period`).

| Iteration | Verdict | LUT | FF | DSP | WNS ns |
|---:|---|---:|---:|---:|---:|
| 0 | seed | 101 | 160 | 6 | -9.943 |
| 1 | timing progress | 150 | 192 | 5 | -9.707 |
| 2 | timing progress | 389 | 192 | 2 | -1.925 |
| 3 | REJECT | 428 | 192 | 2 | -3.983 |
| 4 | **timing recovery** | 212 | 91 | 7 | **+0.267** |
| 5 | REJECT | 235 | 237 | 1 | -0.226 |
| 6 | **objective (final)** | **201** | **32** | 8 | **+0.600** |

Status `done`. Role report: `role-report-fir8.md`.
