# CRC-16/CCITT-FALSE stream (tier 4)

`crc16_stream` transparently wraps one `crc16_stream_core`. Ports: `clk`, `rst`,
`in_data[7:0]`, `in_last`, `in_valid`/`in_ready`, `out_crc[15:0]`, `out_last`,
`out_valid`/`out_ready`. No parameters. Latency 1 (minimum accepted-transfer age).

## Contract

Polynomial 0x1021, init 0xFFFF, no reflection, no final XOR, MSB first. Every
accepted byte produces one output: the CRC of the current frame up to and
including that byte, with `out_last` echoing `in_last`. The byte after an
`in_last=1` byte starts a new frame from 0xFFFF. The check frame `'123456789'`
ends with 0x29B1. One output slot: `in_ready = !out_valid || out_ready`,
full-rate retire/replace, stable payload under stall, no bypass. Synchronous
active-high reset clears the slot and restarts the frame; off-edge reset pulses
change nothing.

One output per accepted byte (rather than one per frame) is deliberate: it keeps
the module inside the harness's scoreboard shape (exactly one output transaction
per input transaction), so the generated golden oracle and generated scoreboard
testbench still apply (`generate_golden: true`).

## What it stresses

- A bit-exact algorithm whose common wrong variants (poly 0x8005, init 0,
  reflected input, missing frame restart) all give plausible 16-bit values.
- State that advances only on accepted bytes and restarts on frame end.
- Exact one-slot ready/valid timing at full rate under backpressure.

## Independent testbench

`crc16_stream_tb.v` keeps its own bit-serial CRC model (a different formulation
from the usual byte-XOR RTL) and self-checks it against 0x29B1 before use. It
models the slot exactly, checks ports before every rising edge and after its
updates, and schedules stimulus from its own model (never from DUT outputs), so a
stuck or hung DUT still reaches a verdict. Coverage: the check string at full
rate, with stalls and noise gaps, and after a mid-frame reset; single-byte
frames; a 40-byte full-rate frame; a reset with an occupied stalled slot and a
blocked byte; four off-edge reset pulses; 1600 seeded random cycles (xorshift32,
simulator independent) with two resets. Behavioral failures print
`FAIL BEHAVIOR rule=...`; checker self-test failures print `CHECKER_FAIL` and
coverage gaps `COVERAGE_FAIL`. The verdict is `TEST PASSED` or
`TEST FAILED: <n> errors`; a watchdog prints `TEST FAILED: watchdog timeout`.

## Qualification (not yet run)

`qualification/reference.v` holds the reference child plus the mechanical top
(byte-identical to `top_verilog(spec)`, enforced by
`tests/test_tier4_fixtures.py`). `qualification/mutants.json` holds ten
single-site faults (`find` occurs exactly once). The testbench must pass the
reference and fail every mutant with a raw `FAIL` assertion, not a watchdog:

```powershell
python curriculum/tier4/qualify_tier4.py curriculum/tier4/crc16_stream_build runs/tier4-qual/crc16_stream
```

No simulation of this fixture has been performed; nothing here is evidence of
compilation, mutant detection or PPA.
