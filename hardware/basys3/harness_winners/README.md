# Every harness winner, on real hardware

This suite runs each design that AutoRTL generated and optimized, unedited
and byte-identical to the archived winner, on a Digilent Basys 3. It checks
every result against an independent reference model, and it stresses each
design's valid/ready handshake far harder than UART traffic alone could.

| Design | Winner (archived, read in place) | Transaction | Status |
|---|---|---|---|
| Signed stateful FIR filter | `generated-signed-fir4-attempt-01` | 1 byte in, 2 out | verified on board |
| Elastic unsigned dot product | `generated-elastic-dot4-attempt-02` | 8 in, 3 out | verified on board |
| Pipelined unsigned dot product | `generated-dot4-attempt-01` | 8 in, 3 out | verified on board |
| Iterative unsigned divider | `generated-divider-attempt-01` | 2 in, 2 out | verified on board |
| Packet-tagged FIFO | `generated-packet-attempt-01` | 2 in, 2 out | verified on board |
| Synchronous FIFO (timing-recovered) | `generated-fifo-attempt-05` | 1 in, 1 out | verified on board |
| Iterative AES-128 encryption (`aes128`) | `2026-11-02/tier6-aes128` | 32 in, 16 out | verified on board |
| Iterative CORDIC sine and cosine (`cordic`) | `2026-11-02/tier6-cordic` | 2 in, 4 out | verified on board |
| Symmetric 16-tap FIR, built for 150 MHz (`fir16_sym`) | `2026-11-02/fir16-ooc-02` | 2 in, 2 out | verified on board |
| Streaming CRC-16/CCITT-FALSE (`crc16_stream`) | `2026-10-30/explore-tier4-02` | 2 in, 3 out | verified on board |
| SPI master, mode 0, with an in-fabric slave (`spi_master`) | `2026-10-30/explore-tier4-02` | 2 in, 2 out | verified on board |
| Multi-cycle RV32I core (`rv32i_core`) | `2026-11-02/tier6-rv32i/explore-tier6-06`, iteration 1 | 32 in, 32 out | verified on board |

The three designs added on November 2 also pass on the board: 50,000 / 50,000 transactions each with 0 mismatches, 10 restarts, and the wrong-model control failing as required (AES-128 build WNS +2.442 ns, CORDIC +1.955 ns, FIR16 +3.066 ns at 100 MHz). Record: [evidence/2026-11-02/basys3-tier56-board-01](../../../evidence/2026-11-02/basys3-tier56-board-01/README.md).
Their transactions:

- **aes128**: bytes 0 to 15 are the key and bytes 16 to 31 the plaintext, each
  in FIPS-197 byte order (byte 0 is the spec's most significant byte, bits
  [127:120]). The 16 result bytes are the ciphertext in the same order. For
  example, FIPS-197 C.1 is sent as `000102...0f` then `00112233...ff`, and
  `69c4e0d8...c55a` comes back.
- **cordic**: a 16-bit binary angle (one turn = 2^16). The result is sin_out
  in bytes 0 and 1, then cos_out in bytes 2 and 3, both Q2.14.
- **fir16_sym**: one signed 16-bit sample in and one output out. Like the
  4-tap FIR, it keeps its history across transactions, and a restart clears
  it. The harness built this winner for 150 MHz; the board runs it at the
  shell's 100 MHz.

All three have full valid/ready handshakes, so their adapters only map ports
and bytes. The AES and CORDIC contracts accept a new input only after the
result transfers, so like the divider they are not required to overlap.
Transactions may be up to 32 bytes on either side.

## Added November 2: CRC-16, SPI master, RV32I

Three more winners pass `python -m hwsuite sim` (the winner matches the model
on 1,200 transactions and the injected fault fails) and pass on the board:
50,000 / 50,000 transactions each with 0 mismatches and 10 restarts, the
wrong-model control failing as required (RV32I build WNS +0.815 ns, CRC-16
+4.052 ns, SPI master +4.131 ns at 100 MHz). The RV32I core ran 50,000
random 8-instruction programs, each checked against an independent ISA
interpreter. Record:
[evidence/2026-11-02/basys3-tier46-board-01](../../../evidence/2026-11-02/basys3-tier46-board-01/README.md).

| Design | Winner file (SHA-256 prefix) | Harness-measured | Simulation | Fault caught |
|---|---|---|---|---|
| `crc16_stream` | `explore-tier4-02/run/crc16_stream_build/crc16_stream_best.v` (`8364cc20`) | 16 LUT / 34 FF | PASS, stalled 254,263, overlap 509 | polynomial 0x8005: 1,194/1,200 wrong |
| `spi_master` | `explore-tier4-02/run/spi_master_build/spi_master_best.v` (`2f2b7fee`) | 19 LUT / 33 FF | PASS, stalled 240,947 | MISO shifted in LSB first: 1,121/1,200 wrong |
| `rv32i_core` | `explore-tier6-06/run/iter_001/cand_standard/rv32i_core.v` (`73f2178b`) | 1,530 LUT / 3,325 FF | PASS, stalled 1,551,112 | BGE compares unsigned: 7/1,200 wrong |

- **crc16_stream**: byte 0 is `in_data` and byte 1 is the last marker (any
  nonzero value sets `in_last`). The result is `out_crc` in bytes 0 and 1 and
  `out_last` (0 or 1) in byte 2. The winner emits one output per accepted
  byte, so one transaction is one winner transfer and the adapter only maps
  ports. Frames are formed by the marker, so, like the FIR filters, the
  winner keeps its frame state across transactions and a restart clears it.
  The model computes CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF, no
  reflection, no final XOR) from its definition; the stimulus starts with
  the frame `123456789`, whose last output is 0x29B1. The wrong twin starts
  frames from 0x0000.
- **spi_master**: byte 0 is `cmd_data` and byte 1 is the byte the slave
  returns. The result is `rsp_data` in byte 0 and the byte the slave captured
  from MOSI in byte 1. The winner's SPI pins stay inside the FPGA and drive a
  small hand-written mode-0 slave in the adapter: it loads its reply when
  `cs_n` falls, shifts MISO after each falling SCLK edge and samples MOSI on
  each rising edge, most significant bit first. It watches the winner's
  registered `sclk` and `cs_n` with the same clock, so it reacts one clock
  after each SCLK edge, which leaves a clock of margin at the winner's
  HALF_PERIOD of 2. The wrong twin shifts least significant bit first. The
  contract accepts a new command only after the response transfers, so it is
  not required to overlap.
- **rv32i_core**: bytes 4n to 4n+3 are instruction word n (n = 0 to 7). The
  core has no handshake, so the adapter runs one program per transaction: it
  resets the core (which clears both memories and the registers), writes the
  8 words through the load port with `run` low (words 8 to 63 stay zero, a
  no-operation), then raises `run` until 32 instructions retire. While the
  program runs, it folds the trace into a signature, with
  `fold(s, w) = rotl(s, 5) ^ w`: each store folds `dmem_addr` then
  `dmem_wdata`, and each retirement folds `pc`, then `32 | rf_waddr` and
  `rf_wdata` when `rf_we` (otherwise 0 and 0). The result is the signature
  in bytes 0 to 3, the clock cycles from `run` to the 32nd retirement in
  bytes 4 to 7, and x1 to x6 in bytes 8 to 31, each least significant byte
  first. A core that never retires stops at 1,023 cycles, so a fault shows
  up as a mismatch instead of a hung board. The model is an ISA-level RV32I
  interpreter written from the spec, not the harness's oracles. The stimulus
  starts with seven directed programs (arithmetic, a backward loop with a
  store and a load, signed and unsigned branches with AUIPC, JALR and JAL,
  address aliasing, shifts, and no-operations), then random 8-word programs
  with forward-only control flow. The wrong twin treats SLT and SLTI as
  unsigned. The fault (BGE compares unsigned) changes a result only when a
  BGE's operands differ in sign and that changes the branch, so it shows on
  few transactions: the directed branch program before and after the restart
  and five random ones.

**The RV32I winner is pinned to an iteration, not a best file.**
`explore-tier6-06` ended on its tool budget (`budget_exhausted`) before it
wrote `rv32i_core_best.v` or a `best_sha256`. Its `state.json` names
`best_iteration` 1, and `designs.json` pins that iteration's candidate with a
`best_pin` entry. Instead of comparing with `best_sha256`, `verify` requires
that `state.json` `best_iteration` is 1, that `iter_001/evaluation_facts.json`
records this file's SHA-256 with simulation passed and timing met, and that
`designs.jsonl` marks iteration 1 accepted and best. Every other design is
still checked against its run's `best_sha256`. The completed
`explore-tier6-08` run (2,027 LUT) was not needed.

## Verified results (October 28, 2026)

All six pass on the board. Full record:
[evidence/2026-10-28/basys3-harness-winners-01](../../../evidence/2026-10-28/basys3-harness-winners-01/README.md).

| Design | Hardware vs model | Wrong model rejected | Injected fault caught | Winner LUT / FF / DSP on board | Harness-measured |
|---|---|---|---|---:|---:|
| Signed FIR | 50,000/50,000, 0 mismatches | 1,990/2,000 differ | 1,190/1,200 wrong | 51 / 67 / 0 | 52 / 67 / 0 |
| Elastic dot product | 50,000/50,000, 0 mismatches | 1,983/2,000 | 1,190/1,200 | 20 / 20 / 4 | 20 / 20 / 4 |
| Pipelined dot product | 50,000/50,000, 0 mismatches | 1,983/2,000 | 1,190/1,200 | 17 / 18 / 4 | 17 / 18 / 4 |
| Iterative divider | 50,000/50,000, 0 mismatches | 2,000/2,000 | 1,200/1,200 | 26 / 30 / 0 | 26 / 38 / 0 |
| Packet FIFO | 50,000/50,000, 0 mismatches | 2,000/2,000 | 584/1,200 | 22 / 29 / 0 | 23 / 31 / 0 |
| Sync FIFO | 50,000/50,000, 0 mismatches | 2,000/2,000 | 41/1,200 | 21 / 13 / 0 | 22 / 13 / 0 |

Each hardware run had 10 restarts. Every build had 0 warnings and met timing
at 100 MHz, with setup slack from +0.965 ns to +4.909 ns.

**The board reproduces the harness's own measurements**, built with each
winner's hierarchy kept. Both dot products match exactly, and the FIR and FIFOs
are within one or two cells. The divider's 8-FF gap is fully explained:
built standalone with the harness's own flow, it has exactly 38 flip-flops.
Those are the same 30 logical registers plus 8 `quotient_work_reg[*]_lopt_replica`
copies that `opt_design` makes because, as a top, the quotient also drives
output ports ([analysis](../../../evidence/2026-10-28/divider-ff-replica-analysis-01/README.md)).

The sync-FIFO fault (a wrong read slot on simultaneous push and pop at
occupancy 2) is caught on only 41 of 1,200 transactions. That is by design: it
only appears under the shaper's backpressure. With a first, correlated shaper it
was not caught at all, which is why the shaper draws its controls from widely
separated LFSR bits.

## How it works

```
PC ── UART ──► byte assembler ─► input FIFO ─► traffic shaper ─► adapter ─► harness winner
PC ◄─ UART ─── serializer ◄──── output FIFO ◄─ traffic shaper ◄─ adapter ◄─┘
```

- **Unedited winners.** Builds and simulations read each winner directly
  from its evidence folder. `designs.json` records its SHA-256, and every
  command first checks that hash against both the file and the run's
  recorded `best_sha256`.
- **Thin adapters** (`adapters/`) only map ports to a common
  `stream_dut` interface. The pipelined dot product has no handshake, so
  its adapter adds a 2-deep valid tag, a 4-entry skid FIFO and credit
  counting, which lets it run under backpressure without dropping a
  result.
- **Generic shell** (`rtl/stream_shell.v`): a transaction is N bytes in and
  M bytes out, least significant byte first. A UART break restarts the
  datapath, so every run starts from reset.
- **Traffic shaper.** UART bytes arrive about 8,700 clocks apart, so on its
  own the link never backs anything up. A 32-bit LFSR adds three kinds of
  legal pressure:
  - random input bubbles, with `in_valid` held once raised, as valid/ready
    requires
  - random `out_ready`
  - long random stall phases, up to 2^18 clocks on hardware, so a queued
    burst then meets a full design

  Each control combines widely separated LFSR bits. Adjacent bits of a
  shift-register LFSR are the same sequence one cycle apart, and the first
  version of this shaper was blind to a FIFO bug for exactly that reason.
- **Independent models** (`hwsuite/models.py`) are written from the
  frozen specifications, not from the harness's generated oracles. Tests
  check them against every I/O example in those specifications. Each model
  has a deliberately wrong twin for negative controls.

## What counts as passing

For each design, all of the following must hold:

1. **Simulation.** 1,200 transactions match the model, with a restart at
   600, through the real shell and shaper.
2. **Coverage.** The design held a result under backpressure for at least
   200 cycles. Where its contract allows it, it also accepted a new input
   while a result retired on at least 20 cycles; the divider's contract
   forbids that.
3. **Fault check.** The same simulation fails on a copy of the winner with
   one fault injected, so the check can actually fail.
4. **Build.** Vivado reports 0 warnings, and setup and hold timing are met
   at 100 MHz. A build that fails only with a known infrastructure message,
   such as a locked scratch directory, is retried once. The failed attempt's
   logs are kept, and the design is never changed.
5. **Hardware.** 50,000 random transactions, with edge cases first and a
   restart every 5,000, return 0 mismatches.
6. **Negative control.** The same hardware results fail against the
   deliberately wrong model.
7. **Traceability.** The archived bitstream's configuration payload equals the
   one programmed for those hardware runs. A .bit header holds the build time,
   so payloads, not file hashes, are compared.

## Run it

From this folder, with Vivado 2025.2 and the board connected:

```powershell
python -m pip install -r requirements.txt      # pyserial, pytest
python -m pytest tests -q                      # no Vivado or board needed
python -m hwsuite verify
python -m hwsuite sim                          # every winner passes, every fault fails
python -m hwsuite all --count 50000            # plus build, program, hardware and negative control
python -m hwsuite evidence --out ../../../evidence/<date>/<new-folder>
```

`--design NAME` limits any command to one design. Set `AUTORTL_VIVADO_BIN`
or pass `--vivado` if Vivado is not at `C:/AMDDesignTools/2025.2/Vivado/bin`.
Vivado use follows the single-queue rule in `docs/AGENT_HANDOFF.md`.

To rerun a board check without synthesis, program the tested bitstream
archived in
[basys3-bitstreams-01](../../../evidence/2026-10-28/basys3-bitstreams-01/README.md)
and test it. Only Vivado's hardware manager is needed:

```powershell
python -m hwsuite program --design sync_fifo --bit ../../../evidence/2026-10-28/basys3-bitstreams-01/harness_winners/sync_fifo.bit
python -m hwsuite hw --design sync_fifo --bit ../../../evidence/2026-10-28/basys3-bitstreams-01/harness_winners/sync_fifo.bit --count 50000
```

`program` writes `build/programmed.json` with the design and payload digest
it loaded. `hw` reports that payload, which equals the one in
`basys3-harness-winners-01/summary.json`, and it refuses to run if the record
names another design or `--bit` names a different image. `--bit` is
accepted only by `program` and `hw`. The record cannot see a board
reprogrammed outside this suite, so delete it after using Vivado's hardware
manager or the UART echo or FIR scripts. A bitstream for the wrong design
also fails the check against that design's model.
[basys3-bitstream-replay-01](../../../evidence/2026-10-28/basys3-bitstream-replay-01/README.md)
replays all six this way.
