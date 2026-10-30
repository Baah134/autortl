# Tier 4 — Harder build entries

Three `build`-mode entries from typed JSON specs, each with an independent
top-level testbench and qualification material:

| Entry | Top | Shape | Generated golden | What it adds over tier 3 |
|---|---|---|---|---|
| `crc16_stream_build` | `crc16_stream` | 1 child, scoreboard, latency 1 | yes | bit-exact CRC with per-frame restart at full rate |
| `spi_master_build` | `spi_master` | 1 child, scoreboard, latency 33, `HALF_PERIOD` | no (trusted TB only) | long cycle-exact serial schedule, parameter-dependent timing, sample instant |
| `rr_regfile_build` | `rr_regfile` | 2 children, fixed latency, 3 connections | yes (per child) | internal write bus, fairness state, read-first ordering, top wiring |

Each entry's `qualification/reference.v` holds the reference children plus the
mechanical top (byte-identical to `top_verilog(spec)`), and
`qualification/mutants.json` holds single-site `find`/`replace` faults. Qualify a
testbench with Vivado before trusting it:

```powershell
python curriculum/tier4/qualify_tier4.py curriculum/tier4/<entry> runs/tier4-qual/<entry>
```

The control must print `TEST PASSED`; every mutant must produce a raw `FAIL`
line and `TEST FAILED` (a watchdog or compile error is not a detection).
`tests/test_tier4_fixtures.py` checks the static invariants only. None of these
testbenches has been simulated yet.

Planned later: RTLLM v2 / VerilogEval-Human alignment problems (compare LUT/FF
reductions with CRADLE's published 48% LUT / 40% FF on RTLLM), added as further
entry folders once these entries are qualified.
