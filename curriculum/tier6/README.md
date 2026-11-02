# Tier 6 — Hardest build entries

Three `build`-mode entries from typed JSON specs, each with an independent
top-level testbench and qualification material, in the tier4/tier5 format:

| Entry | Top | Shape | Port bits / flow | What it adds over tier 5 |
|---|---|---|---|---|
| `rv32i_core_build` | `rv32i_core` | 6 children (2 combinational), 26 connections | 151 / out of context | multi-cycle RV32I subset (ALU, immediates, LUI/AUIPC, JAL/JALR, six branches, LW/SW); instruction and data memories; an ISA-level reference model with hand-assembled and random programs |
| `aes128_core_build` | `aes128_core` | 3 children (2 combinational), 7 connections, 128-bit buses | 390 / out of context | iterative AES-128 with on-the-fly key expansion; FIPS-197 and AESAVS known answers and back-to-back random blocks against an independent behavioral cipher |
| `cordic_build` | `cordic_sincos` | 4 children (3 combinational), 6 connections | 54 / chip top | bit-exact 16-step CORDIC sine/cosine with stated fixed-point formats, plus a loose check against true sin and cos |

All entries set `generate_golden: true`, `iterations: 4`, `objective:
minimize_luts`, 100 MHz and `pass_criteria: timing_met`. A multi-module build
sends every child through the generated golden path, so each child is either a
cycle-level fixed-latency module (latency 1, every output a view of registered
state, synchronous active-high `rst`) or, new in this tier, a purely
combinational child (latency 0, no clock or reset port). Every port is
`protocol: none`; handshake ports keep their valid/ready meaning and the
independent testbenches check them cycle-exactly. Spec examples hold constant
integer inputs for `after_cycles` steps from reset (at most 20 here).
`implementation: out_of_context` is set exactly for the tops whose port bits
exceed the 106 user I/O of xc7a35tcpg236-1 (taxonomy
`chip_top_flow_for_soc_block`).

Each entry's `qualification/reference.v` holds the reference children plus the
mechanical top (byte-identical to `top_verilog(spec)`), and
`qualification/mutants.json` holds ten single-site `find`/`replace` faults.
`qualify_tier6.py` reuses `curriculum/tier4/qualify_tier4.py` unchanged:

```powershell
python curriculum/tier6/qualify_tier6.py curriculum/tier6/<entry> <absolute out dir>
```

## Qualification results (Vivado 2025.2 xsim, no synthesis)

Every reference prints `TEST PASSED`; every mutant prints raw `FAIL BEHAVIOR`
lines and `TEST FAILED` without a watchdog. Error counts per mutant are in each
entry's `qualification/console.txt`, and `qualification/qualification.json`
records the testbench and per-case source hashes (over the LF bytes as
committed).

| Entry | Reference | Mutants detected | Simulated cycles (reference) |
|---|---|---|---|
| `rv32i_core_build` | TEST PASSED | 10 / 10 | 13,937 (2,556 instructions retired, 45 programs) |
| `aes128_core_build` | TEST PASSED | 10 / 10 | 7,286 (525 blocks accepted, 15 known answers) |
| `cordic_build` | TEST PASSED | 10 / 10 | 33,047 (1,797 angles; worst loose error 2.19 LSB) |

That is evidence about these testbenches against these references and faults:
it is not synthesis, timing, PPA or a harness build. No tier6 entry has been
synthesized or run through `run.py build` yet.

`tests/test_tier6_fixtures.py` checks the static invariants, the recorded
qualification, hand-written test-only oracles that agree with every spec example
and fit the generated testbench path, and that those oracles compose into a
working core, the FIPS-197 C.1 ciphertext and sin/cos within 4 LSB.

Candidates for later entries: an asynchronous FIFO as the CDC exam, a pipelined
RV32I with hazards and forwarding, a memory arbiter.
