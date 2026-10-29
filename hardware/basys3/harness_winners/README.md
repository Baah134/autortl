# Every harness winner, on real hardware

This suite runs each design that AutoRTL generated and optimized, unedited
and byte-identical to the archived winner, on a Digilent Basys 3. It checks
every result against an independent reference model, and it stresses each
design's valid/ready handshake far harder than UART traffic alone could.

| Design | Winner (archived, read in place) | Transaction |
|---|---|---|
| Signed stateful FIR filter | `generated-signed-fir4-attempt-01` | 1 byte in, 2 out |
| Elastic unsigned dot product | `generated-elastic-dot4-attempt-02` | 8 in, 3 out |
| Pipelined unsigned dot product | `generated-dot4-attempt-01` | 8 in, 3 out |
| Iterative unsigned divider | `generated-divider-attempt-01` | 2 in, 2 out |
| Packet-tagged FIFO | `generated-packet-attempt-01` | 2 in, 2 out |
| Synchronous FIFO (timing-recovered) | `generated-fifo-attempt-05` | 1 in, 1 out |

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

`hw` records the payload digest of the `--bit` file; it equals the one in
`basys3-harness-winners-01/summary.json`. A bitstream for the wrong design
fails the check against that design's model.
