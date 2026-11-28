# Tier5 fir16_sym_build: 150 MHz closed out of context

A long run of the hardest timing target in the curriculum: a 16-tap symmetric
FIR on a valid/ready stream, latency fixed at 5 by the spec, at 150 MHz on the
xc7a35tcpg236-1.

```
python run.py build --spec curriculum/tier5/fir16_sym_build/design_spec.json
  --tb curriculum/tier5/fir16_sym_build/fir16_sym_tb.v --top fir16_sym --generate-golden
  --implementation out_of_context --iterations 10 --best-of-n 1 --objective minimize_luts
  --max-llm-calls 80 --max-vivado-minutes 150 --max-wall-minutes 240
  --target-freq-mhz 150 --model gpt-6-luna (Vivado 2025.2)
```

Code: main checkout at af8253d6 (awake-clock budgets), with the out-of-context
flow for this entry (4df373f0). Earlier attempts: explore-tier5-01 (chip-top,
-3.02 ns), fir16-long-01 (chip-top, stopped: the worst path was register ->
in_ready pin, a pad-delay floor above the 6.67 ns period; taxonomy
`chip_top_pad_floor_exceeds_period`), fir16-ooc-01 (ended by a host sleep;
taxonomy `host_sleep_charged_to_run_budget`).

| Iteration | Verdict | LUT | FF | DSP | WNS ns | WHS ns |
|---:|---|---:|---:|---:|---:|---:|
| 0 | built from spec | 394 | 325 | 7 | -10.250 | 0.122 |
| 1 | timing progress | 161 | 299 | 8 | -9.368 | 0.108 |
| 2 | REJECT | 189 | 308 | 8 | -2.433 | 0.025 |
| 3 | timing progress | 161 | 278 | 8 | -5.856 | 0.122 |
| 4 | **timing recovery** | 160 | 261 | 9 | **+1.075** | 0.153 |
| 5 | objective | 150 | 261 | 9 | +1.010 | 0.152 |
| 6 | objective | 149 | 261 | 9 | +1.075 | 0.118 |
| 7, 8, 10 | REJECT | | | | | |
| 9 | **objective (final)** | **148** | 277 | 9 | **+0.751** | 0.023 |

Status `done`, 36 model calls, about 68 minutes of tool time. Every accepted
step passed the independent testbench (qualified in xsim against ten faults).

Iteration 2 shows a harness rule since fixed: it cut the deficit to -2.433 ns
with hold still met (+0.025 ns), but its hold slack fell more than the 0.05 ns
progress tolerance, so it was discarded (taxonomy
`met_hold_counted_as_regression`, fixed in 4c50e34d after this run started).

Role report: `role-report.md`.
