# Iterative CORDIC sine and cosine (tier 6)

`cordic_sincos` mechanically wires four generated children:

| Child | Kind | Role |
|---|---|---|
| `cordic_prerot` | combinational, latency 0 | quadrant fold: start `x0 = +-K`, residual angle `z0` |
| `cordic_atan` | combinational, latency 0 | 16-entry arctangent table indexed by the iteration |
| `cordic_engine` | cycle-level, latency 1 | handshake and sixteen micro-rotations, one per edge |
| `cordic_out` | combinational, latency 0 | Q2.16 to Q2.14 with round half up |

Six connections. Top ports: `clk`, `rst`, `angle[15:0]`, `in_valid`/`in_ready`,
`out_valid`/`out_ready`, `cos_out[15:0]`, `sin_out[15:0]` (54 port bits, so this
is a chip top in the default flow). Handshake ports are protocol none, as in the
other multi-module entries.

## Contract (bit exact)

- `angle`: 16-bit binary angle, theta = angle * 2*pi / 2^16 (one turn = 2^16).
- `x`, `y`: 18-bit Q2.16; `z` and the table: 20-bit, units of 2^-20 turn;
  `cos_out`, `sin_out`: 16-bit Q2.14. All two's complement.
- Fold: quadrants 01 and 10 (|theta| >= pi/2) start at `x0 = -K` with the angle
  XOR 0x8000 (half a turn); otherwise `x0 = K`. `K = 39797 = round(2^16 * prod
  1/sqrt(1 + 2^-2i))` for i = 0..15. `z0 = {reduced angle, 4'b0000}`, `y0 = 0`.
- Table: `round(atan(2^-i) / (2*pi) * 2^20)` = 131072, 77376, 40884, 20753,
  10417, 5213, 2607, 1304, 652, 326, 163, 81, 41, 20, 10, 5.
- Iteration i (0..15): `xs = x >>> i`, `ys = y >>> i` (arithmetic, toward minus
  infinity); `z >= 0` rotates up (`x - ys`, `y + xs`, `z - atan`), otherwise down.
- Output: `(v + 2) >>> 2` over 19 bits, low 16 bits.
- Handshake: accept when idle; 16 busy edges; `out_valid` until the transfer;
  `in_ready = !busy && !out_valid` (18 cycles per angle at full rate).

Over all 65536 angles this contract stays within 3.3 Q2.14 LSB of the true
cosine and sine (computed offline in double precision), so the testbench's loose
bound is 4 LSB.

## Independent testbench

`cordic_sincos_tb.v` has two references. The bit-exact one re-implements the
contract with 32-bit integers and explicit wrapping and is compared on every
result. The loose one evaluates cos and sin by Taylor series (no system math
functions) and requires every transferred result within 4 LSB, which catches a
table or gain error that the design and the exact model could share. At time 0
it also recomputes the arctangent table (series arctangent, Machin's pi) and
checks the gain's rounding interval. Angles: 24 quadrant and octant boundaries,
a stride-61 sweep of the whole circle (1075 angles) and seeded random angles,
under random valid gaps, noise on `angle` while not offering, offers held during
busy, output backpressure, a reset mid-rotation, a reset with an output pending
and two off-edge reset pulses. The handshake is checked before every rising edge.

## Qualification (run)

`qualification/reference.v` holds the four reference children and the
mechanical top (byte-identical to `top_verilog(spec)`); `qualification/mutants.json`
has ten single-site faults: two table errors (one only the exact check can see),
a logical shift, `z > 0` instead of `z >= 0`, folding on the sign bit, a
truncated gain, an unscaled `z0`, truncation instead of rounding, fifteen
iterations and a flipped `y` update.

```powershell
python curriculum/tier6/qualify_tier6.py curriculum/tier6/cordic_build <absolute out dir>
```

Run in Vivado 2025.2 xsim (no synthesis): the reference passes and every mutant
fails with raw `FAIL BEHAVIOR` lines and no watchdog; see
`qualification/qualification.json` and `qualification/console.txt`. No
synthesis, implementation or harness build of this entry has run.
