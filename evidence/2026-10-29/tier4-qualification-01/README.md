# Tier4 testbench qualification: 3 of 3 qualified, 30 of 30 mutants caught

The three new tier4 entries (CRC-16/CCITT-FALSE stream, SPI mode-0 master,
round-robin arbiter feeding a register file) were written with a correct
reference design and ten deliberate single-fault mutants each. Before any
tier4 entry may grade the harness, its independent testbench must pass the
reference and fail every mutant, by an explicit `FAIL` assertion plus
`TEST FAILED`, never by a watchdog or a compile error.

| Entry | Reference | Mutants caught | Testbench SHA-256 |
|---|---|---:|---|
| crc16_stream_build | TEST PASSED | 10 / 10 | `a90ca8b0fbe4…` |
| spi_master_build | TEST PASSED | 10 / 10 | `2db6641d00f0…` |
| rr_regfile_build | TEST PASSED | 10 / 10 | `83456a9774c8…` |

Run with `curriculum/tier4/qualify_tier4.py` (xvlog, xelab, xsim from Vivado
2025.2) on branch `worktree-agent-a58ccba2472b5b897` at ffc75f0. Each
`run/<entry>/qualification.json` records every case: its source digest, the
simulator verdict, and whether it behaved as required; the per-case folders
hold the simulation logs.

The mutants, by name:
- **CRC:** wrong polynomial, zero initial value, reset that keeps the frame,
  no restart after the last byte, reflected input bits, capture while
  blocked, a throughput bubble, a dropped last flag, valid dropped under
  stall, asynchronous reset.
- **SPI master:** received LSB first, sampling on the falling edge, a half
  period one cycle long, the divider parameter ignored, MOSI shifted on the
  rising edge, a seven-bit transfer, accepting while a response is held, a
  response dropped under stall, reset that keeps the transfer, asynchronous
  reset.
- **Arbiter and register file:** fixed priority, pointer reset to zero,
  re-granting the same requester, an off-by-one data select, a binary
  instead of one-hot grant, a write-first bypass, a write that ignores
  enable, reset that keeps memory, asynchronous register-file reset, a
  miswired top-level read address.
