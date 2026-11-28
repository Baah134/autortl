# RV32I core, CRC-16 stream and SPI master on the Basys 3

Three more harness winners, run unedited with the harness-winners suite (merged
at 2eea8ecf): `python -m hwsuite all --design <name> --port COM10 --count
50000`, then `python -m hwsuite evidence`. Programming is volatile (JTAG); the
configuration flash was not touched.

| Design (winner, read in place) | Transaction | Simulation (1,200, restart at 600) | Injected fault | Build at 100 MHz | Board: 50,000, restart every 5,000 | Wrong-model control (2,000) |
|---|---|---|---|---|---|---|
| RV32I core, 1,530 LUT (`tier6-rv32i/explore-tier6-06`, iteration 1, pinned by `best_pin`) | 32 bytes in (8 instructions), 32 out (trace signature, cycles, x1-x6) | PASS, held 1,551,112 cycles | BGE compares unsigned: 7 wrong (only mixed-sign operands expose it) | WNS +0.815 ns, WHS +0.037 ns | **50,000 / 50,000 programs, 0 mismatches** | FAIL as required, 1,318 differ |
| CRC-16/CCITT-FALSE stream (`explore-tier4-02`) | 2 in (byte, last), 3 out (CRC, last) | PASS, held 254,263, overlap 509 | polynomial 0x8005: 1,194 wrong | WNS +4.052 ns, WHS +0.037 ns | **50,000 / 50,000, 0 mismatches** | FAIL as required, 2,000 differ |
| SPI master, mode 0, with an in-fabric slave (`explore-tier4-02`) | 2 in (command, slave reply), 2 out (response, slave capture) | PASS, held 240,947 | MISO shifted LSB first: 1,121 wrong | WNS +4.131 ns, WHS +0.086 ns | **50,000 / 50,000, 0 mismatches** | FAIL as required, 1,989 differ |

The RV32I adapter loads each program through the core's instruction-memory
load port, runs it to 32 retirements (or a 1,023-cycle limit) and returns a
trace signature folded from every retirement and store, the cycle count and
x1-x6; the independent model is an ISA-level interpreter written from the
specification, fed seven directed programs and random forward-branching
programs. The SPI adapter contains a hand-written mode-0 slave; the CRC model
computes CRC-16/CCITT-FALSE from its definition (check value 0x29B1 for
"123456789", sent first).

Folders: one per design from `hwsuite evidence`, plus `bitstreams/`.
