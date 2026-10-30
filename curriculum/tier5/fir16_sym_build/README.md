# 16-tap symmetric FIR stream (tier 5)

`fir16_sym` transparently wraps one `fir16_sym_core`. Ports: `clk`, `rst`,
signed `in_sample[15:0]`, `in_valid`/`in_ready`, signed `out_sample[15:0]`,
`out_valid`/`out_ready`. No parameters. Latency 5 (minimum accepted-transfer
age). Target 150 MHz.

## Contract

Coefficients `-6, -20, -24, 18, 110, 226, 330, 390` and their mirror image
(h[k] = h[15-k], sum 2048). For each accepted sample, acc = sum h[k]*x[n-k]
over the accepted history (zeros after reset); r = (acc + 1024) >>> 11 (round
half up); out_sample = r saturated to [-32768, 32767]. Pairwise pre-adder sums
need 17 bits and |acc| fits in 28 signed bits.

Five elastic slots: `ready5 = !v5 || out_ready`, `ready_i = !v_i || ready_(i+1)`,
`in_ready = ready1`, `out_valid = v5`. A sample accepted at edge k can transfer
at edge k+5 at the earliest; one sample per cycle at full rate; bubbles collapse,
so `in_ready` is 0 only with all five slots full and `out_ready` low. A stalled
output is stable. Synchronous active-high reset empties the slots and clears the
history; off-edge pulses change nothing.

`generate_golden: true`: the module is in the scoreboard shape (exactly one
input and one output valid/ready channel, one output per accepted input), so a
transaction-level Python oracle can describe it, as for tier3 `signed_fir4`.

## What it stresses

- Arithmetic whose wrong variants look right on typical data: a 16-bit
  pre-adder, truncation instead of rounding, wrap instead of saturation, a
  mispaired tap, one wrong coefficient sign.
- Exact elastic-pipeline timing with bubble collapse, which a global-stall
  pipeline does not meet.
- Optimization pressure: eight constant multiplies (DSP48 versus LUT
  shift-add), a pre-adder, an adder tree and saturation at 150 MHz.

## Independent testbench

`fir16_sym_tb.v` evaluates the filter in direct form (sixteen products, no
pre-adder) over its own accepted history, models the five slots abstractly and
checks `in_ready`, `out_valid` and `out_sample` before and after every rising
edge. Coverage: impulse responses of both signs, impulses of +/-512 that make
exact rounding ties, constant extremes (17-bit pre-adder sums, both rails),
windows aligned with the coefficient signs (|acc| above 70 million), alternating
extremes, a full stalled pipeline with a blocked sample held five cycles, sparse
input behind an intermittently stalled output (bubble collapse), a synchronous
reset with nonzero history, off-edge reset pulses with a full pipeline, and 2000
seeded random cycles (xorshift32) with two resets. Stimulus follows the model,
never DUT outputs.

## Qualification (not yet run)

`qualification/reference.v` is the reference child plus the mechanical top
(byte-identical to `top_verilog(spec)`); `qualification/mutants.json` has ten
single-site faults.

```powershell
python curriculum/tier5/qualify_tier5.py curriculum/tier5/fir16_sym_build runs/tier5-qual/fir16_sym
```

No simulation of this fixture has been performed. A hand-written Python
emulation of the testbench schedule, the reference and the mutants (not
committed) agreed with the reference and caught all ten mutants. That is not
evidence of compilation, simulator behavior, mutant detection or PPA.
