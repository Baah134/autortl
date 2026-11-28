# AXI4-Lite register slave (tier 5)

`axil_regs` mechanically wires three generated children:

| Child | Inputs | Outputs (views of registered state) |
|---|---|---|
| `axil_wr_if` | AW, W, `bready` | `awready`, `wready`, `bvalid`, `bresp` (external), `wr_en`, `wr_idx[2:0]`, `wr_data[31:0]`, `wr_strb[3:0]` |
| `axil_regbank` | write port (from `axil_wr_if`), `irq_set[7:0]`, `status_in[31:0]` | `regs_flat[255:0]`, `ctrl[31:0]`, `irq` (external) |
| `axil_rd_if` | AR, `rready`, `regs_flat` (from the bank) | `arready`, `rvalid`, `rdata`, `rresp` (external) |

Five explicit connections: the four write-port signals and the 256-bit
`regs_flat` view. All children are fixed-latency 1 cycle-level modules with
synchronous active-high reset; there is no top latency annotation.

## Contract (cycle exact)

6-bit byte addresses; bit 5 set (0x20..0x3F) is out of range and answers
SLVERR (`2'b10`) with no register change and `rdata = 0`; bits 1:0 are ignored.

Registers: 0 CTRL (RW, drives `ctrl`), 1 SCRATCH (RW), 2 CONFIG (RW, reset
0x100), 3 IRQ_MASK (bits 7:0, lane 0 only), 4 IRQ_STATUS (bits 7:0, set by
`irq_set`, write-1-to-clear on lane 0; set wins), 5 STATUS (RO, `status_in`
registered every cycle), 6 ID (RO, 0x52544C35), 7 WRITE_COUNT (RO, counts every
in-range write including writes to read-only registers). Byte strobes apply to
the RW registers. `irq = |(IRQ_STATUS & IRQ_MASK)`.

Write side: `awready = !aw_full`, `wready = !w_full`; AW and W are captured
independently in either order. A held pair is written at the next edge where
`bvalid` was 0, and the register update and `bvalid` appear after that same
edge, so a master that reads after B always sees the new value. Read side:
`arready = !rvalid`; the accepted read samples the registers as they were before
its edge (a read accepted at the write edge returns the old value); `rdata` and
`rresp` hold under backpressure.

## Implemented out of context

An AXI4-Lite slave is a block inside an SoC, not a chip top. Its ports add up
to 169 bits, and the Basys 3 part (xc7a35tcpg236-1) has 106 user I/O, so the
chip-top flow can never place it: explore-tier5-01 and explore-tier5-02 passed
the independent testbench, then failed placement with `[Place 30-415]`
(Vivado counted 165 I/O ports), and the fix loop broke the correct design
(taxonomy `io_overutilization_sent_to_fixer`; that failure now stops the run
as `target_infeasible`).

`meta.yaml` therefore sets `implementation: out_of_context`
(`run.py build --implementation out_of_context`; taxonomy
`chip_top_flow_for_soc_block`). Synthesis runs with
`synth_design -mode out_of_context`, so no I/O buffers are inserted and the
utilization has no IOBs. `clk` is constrained at the target period (100 MHz)
and modeled as driven by a global clock buffer. The data ports have no input or
output delay and no pad delay: setup WNS and hold WHS, which the acceptance
gate requires to be at least 0, cover the routed internal clocked paths only.
The combinational logic between a port and its first or last register is not
timed. That flow has not run on this entry yet.

## Why the handshake ports are tagged `protocol: none`

A multi-module build sends every child through the generated golden path. An
AXI slave has five channels, so no child fits the scoreboard shape (exactly one
input and one output valid/ready channel). Each child is therefore a
cycle-level fixed-latency module whose outputs depend only on registered state;
its generated testbench compares every output every cycle. The ports keep AXI
semantics and this testbench checks them exactly.

## What it stresses

- Handshake independence (a ready that waits for the other channel's valid is a
  classic bug that still works with most masters).
- A held write behind a stalled response; read data stability under
  backpressure while the next ARVALID is already high.
- Decode faults that look right on aligned in-range traffic: low-bit indexing,
  out-of-range aliasing on write or read, a missing SLVERR.
- Register semantics: byte strobes, write-1-to-clear with set priority, masked
  interrupt, read-only registers that still count writes.
- Integration of three children through a 256-bit internal bus.

## Independent testbench

`axil_regs_tb.v` acts as an AXI master that keeps every offered VALID and
payload stable until accepted (reset aside). It models the held AW/W halves,
B and R and all eight registers, and checks every output before and after each
rising edge. Coverage: reset values; each writable register; W before AW and
AW before W; stalled B; a second pair held behind a stalled B; all sixteen
strobe patterns with read-back; out-of-range writes aliasing every index and
out-of-range reads; unaligned addresses; interrupt set, mask, clear, lane-0
gating and set-and-clear at one edge; read-only writes; a read at the edge a
write lands; a held ARVALID behind a stalled R; a synchronous reset with every
channel busy; off-edge reset pulses; 3000 seeded random master cycles
(xorshift32) with three resets. Stimulus never depends on DUT outputs.

## Qualification (not yet run)

`qualification/reference.v` holds the three reference children and the
mechanical top (byte-identical to `top_verilog(spec)`); `qualification/mutants.json`
has ten single-site faults across the write engine, the bank and the read engine.

```powershell
python curriculum/tier5/qualify_tier5.py curriculum/tier5/axil_regs_build runs/tier5-qual/axil_regs
```

No simulation of this fixture has been performed. A hand-written Python
emulation of the testbench schedule, the reference and the mutants (not
committed) agreed with the reference and caught all ten mutants. That is not
evidence of compilation, simulator behavior, mutant detection or PPA.
