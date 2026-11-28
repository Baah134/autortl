# Tier6 aes128_core_build: AES-128 built and optimized

Exploratory, not a curriculum verdict: `tools/explore.py --tier 6 --entries
cordic_build aes128_core_build --name explore-tier6-07 --jobs 2 --model
gpt-6-luna` on the main checkout at c5335c1c (entry settings: out of context,
45-minute synthesis limit, 150 tool / 240 wall minutes). Only the AES entry of
that exploration is archived here; its CORDIC run was stopped and rerun on a
fixed rule (see `tier6-cordic`).

The design: an iterative AES-128 encryptor split by the planner-free typed spec
into a sequencer, a combinational round and a combinational key-schedule step,
one key-preparation edge plus ten round edges. Every accepted step passed the
independent testbench: FIPS-197 C.1 and Appendix B, AESAVS GFSbox, KeySbox,
VarTxt and VarKey known answers (15 in all) and about 525 random blocks back to
back under backpressure and resets, qualified in xsim against ten faults.

| Iteration | Verdict | LUT | FF | WNS ns (100 MHz) |
|---:|---|---:|---:|---:|
| 0 | built from the typed spec | 9,108 | 262 | -9.760 |
| 1 | **timing recovery** | 627 | 262 | +2.270 |
| 2 | **objective (final)** | **614** | 262 | **+2.216** |
| 3, 4 | REJECT (larger) | 1,329 / 1,105 | 262 | met |

Status `done`, 18 model calls.

## How the harness got here

Four earlier attempts each exposed a gap, now fixed (taxonomy entries):

- `golden_table_setup_exhausts_step_budget`: the round oracle's table setup
  shared one 200,000-line budget with every step; setup now has its own.
- `golden_step_budget_below_wall_timeout`: a correct AES round oracle needs
  ~5,600 traced lines per cycle but runs 120 cycles in 0.28 s; the step budget
  is now sized against the 5 s wall timeout.
- `golden_attempts_too_few_for_table_math`: one oracle built inverses with 254
  multiplications per entry, another slipped in its log tables; oracles now
  get three attempts and the prompt names efficient table constructions.
- `fixed_synthesis_timeout_blocks_heavy_designs`: the verified baseline's
  synthesis passed the fixed 900 s limit; entries can now raise it.

Role report: `role-report.md`.
