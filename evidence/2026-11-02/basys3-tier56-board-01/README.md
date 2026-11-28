# AES-128, CORDIC and the 150 MHz FIR on the Basys 3

The three newest harness winners, run unedited on the board with the
harness-winners suite (`hardware/basys3/harness_winners`, merged at 514d8f50):
`python -m hwsuite all --design <name> --port COM10 --count 50000`, then
`python -m hwsuite evidence`. Programming is volatile (JTAG); the
configuration flash was not touched.

| Design (winner, read in place) | Transaction | Simulation (1,200, restart at 600) | Injected fault | Build at 100 MHz | Board: 50,000 random, edge cases first, restart every 5,000 | Wrong-model control (2,000) |
|---|---|---|---|---|---|---|
| AES-128 (`evidence/2026-11-02/tier6-aes128`) | 32 bytes in (key, plaintext), 16 out | PASS, held 1,515,592 cycles under backpressure | ShiftRows rotates right: 1,200 / 1,200 wrong | WNS +2.442 ns, WHS +0.049 ns | **50,000 / 50,000, 0 mismatches**, 10 restarts | FAIL as required, 1,582 differ |
| CORDIC sin/cos (`evidence/2026-11-02/tier6-cordic`) | 2 in (angle), 4 out (sin, cos) | PASS, held 278,446 cycles | cos rounding +1 not +2: 305 wrong | WNS +1.955 ns, WHS +0.074 ns | **50,000 / 50,000, 0 mismatches**, 10 restarts | FAIL as required, 1,967 differ |
| 16-tap symmetric FIR, built for 150 MHz (`evidence/2026-11-02/fir16-ooc-02`) | 2 in, 2 out, stateful | PASS, held 247,269 cycles, 298 overlap cycles | tap-pair-3 sign flipped: 859 wrong | WNS +3.066 ns, WHS +0.037 ns | **50,000 / 50,000, 0 mismatches**, 10 restarts | FAIL as required, 1,883 differ |

The independent models in `hwsuite/models.py` are written from each entry's
specification, not from the harness's oracles: AES-128 computes its S-box from
the GF(2^8) inverse and is checked against FIPS-197 C.1, Appendix B and AESAVS
answers; CORDIC is a bit-exact integer model with its arctangent table and gain
computed from their definitions; the FIR is a direct-form model. Each has a
deliberately wrong twin, used for the negative control above.

AES-128 needed 32-byte transactions, so the suite's shell limit was raised
from 8 to 32 bytes (designs.py, build.tcl and the shell bench).

Folders: one per design from `hwsuite evidence` (summary, manifest, sim,
fault, implementation and hardware logs), plus `bitstreams/` holding the three
programmed images.
