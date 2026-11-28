# Iterative AES-128 encryption core (tier 6)

`aes128_core` mechanically wires three generated children:

| Child | Kind | Role |
|---|---|---|
| `aes_ctrl` | cycle-level, latency 1 | handshake, state register `ct`, round key `rk`, round counter; drives `rcon` and `last` |
| `aes_round` | combinational, latency 0 | SubBytes, ShiftRows, MixColumns (skipped when `final_round`), AddRoundKey |
| `aes_key_step` | combinational, latency 0 | next round key: RotWord, SubWord, rcon, word chain |

Seven connections: `ct`, `rk` and `last` into the round, `rk` and `rcon` into the
key step, `state_out` and `key_out` back to the sequencer. Top ports: `clk`,
`rst`, `in_valid`/`in_ready`, `key[127:0]`, `pt[127:0]`, `out_valid`/`out_ready`,
`ct[127:0]`; the handshake ports are protocol none (a multi-module build sends
every child through the generated fixed-latency path, and the sequencer's
neighbour ports make it unfit for the scoreboard shape).

## Contract

Blocks are big-endian byte strings (byte 0 is bits [127:120], byte n at row
n % 4, column n / 4), as in FIPS-197. On the accepting edge `ct = pt ^ key` and
`rk = key`. The next edge is key preparation (`rk = K1`), then rounds 1..10 each
take one edge with the round key already registered (`last` selects the final
round without MixColumns), so the round's critical path does not include the key
schedule. `out_valid` with the ciphertext on `ct` appears after the 11th busy
edge and holds under backpressure; `in_ready = !busy && !out_valid`, so the next
block is accepted at the edge after the output transfer at the earliest (13
cycles per block at full rate). `key`, `pt` and `in_valid` are ignored except
at the accepting edge.

## Implemented out of context

Three 128-bit buses make 390 port bits against 106 user I/O on xc7a35tcpg236-1,
so `meta.yaml` sets `implementation: out_of_context` (taxonomy
`chip_top_flow_for_soc_block`). Paths from ports to the first register are not
timed in that flow; the round and key step sit between registers and are timed.

## Independent testbench

`aes128_core_tb.v` builds its own S-box at time 0 from the GF(2^8) inverse and the
affine map, expands keys as in FIPS-197 section 5.2 and computes MixColumns with
a general field multiply; nothing is shared with the reference design. That
model is checked against 15 known answers (FIPS-197 C.1 and Appendix B, AESAVS
GFSbox, KeySbox, VarTxt and VarKey entries, all confirmed against an independent
library before inclusion), and those blocks are sent to the DUT and compared with
the published ciphertext directly. Then about 500 seeded random blocks (plus
all-zero keys and all-ones plaintexts) run back to back with random valid gaps,
noise on `key`/`pt` while not offering, offers held during busy, random output
backpressure, a reset mid-block, a reset with an output pending and two off-edge
reset pulses. `in_ready`, `out_valid` and `ct` are checked before every rising
edge against a cycle model of the contract.

## Qualification (run)

`qualification/reference.v` holds the three reference children and the
mechanical top (byte-identical to `top_verilog(spec)`); `qualification/mutants.json`
has ten single-site faults: an S-box entry, ShiftRows direction, a MixColumns
coefficient, MixColumns in the final round, an unreduced rcon, a missing
RotWord, a wrong key-word chain, a missing initial AddRoundKey, `in_ready` while
busy and an output dropped under backpressure.

```powershell
python curriculum/tier6/qualify_tier6.py curriculum/tier6/aes128_core_build <absolute out dir>
```

Run in Vivado 2025.2 xsim (no synthesis): the reference passes and every mutant
fails with raw `FAIL BEHAVIOR` lines and no watchdog; see
`qualification/qualification.json` and `qualification/console.txt`. No
synthesis, implementation or harness build of this entry has run.
