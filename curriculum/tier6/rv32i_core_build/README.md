# Multi-cycle RV32I core (tier 6)

`rv32i_core` mechanically wires six generated children:

| Child | Kind | Role |
|---|---|---|
| `rv_imem` | cycle-level, latency 1 | 64 x 32 instruction memory: load port (`imem_we`, `imem_waddr`, `imem_wdata`) and a registered read-first read port |
| `rv_decode` | combinational, latency 0 | fields, I/S/B/U/J immediates, `alu_op`, `a_sel`, `b_sel`, `kind`, `funct3` |
| `rv_regfile` | cycle-level, latency 1 | x0..x31, x0 reads 0, two registered read-first read ports, one write port |
| `rv_alu` | combinational, latency 0 | operand select (rs1, pc or 0; rs2 or imm), ten operations, raw `eq`/`lt`/`ltu` of rs1 and rs2 |
| `rv_dmem` | cycle-level, latency 1 | 32 x 32 data memory, one address, registered read-first read |
| `rv_ctrl` | cycle-level, latency 1 | sequencer F, D, E, (M, L), W: pc, next pc, result, store data |

26 explicit connections. Top ports: `clk`, `rst`, `run`, the load port, and a
trace of every architectural effect: `pc`, `retire`, `rf_we`/`rf_waddr`/`rf_wdata`
and `dmem_we`/`dmem_addr`/`dmem_wdata`. No top latency annotation.

## Contract

Subset: ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND; ADDI, SLTI, SLTIU,
XORI, ORI, ANDI, SLLI, SRLI, SRAI; LUI, AUIPC, JAL, JALR; BEQ, BNE, BLT, BGE,
BLTU, BGEU; LW and SW. Resolved choices (each child's behavior text states them):

- Harvard, both memories inside. Instruction word `pc[7:2]`; data word
  `address[6:2]`. Address bits [1:0] are ignored (no misalignment trap) and higher
  bits alias. Every LOAD is a word load and every STORE a word store (funct3
  ignored); JALR ignores funct3.
- Branch funct3 010 and 011 are never taken; FENCE, SYSTEM and every unknown
  opcode are no-operations (kind 6). R-type decode uses funct3 and `instr[30]`
  only; OP-IMM uses `instr[30]` only for SRLI/SRAI.
- Memories and registers are cleared by the synchronous reset, not by initial
  values: AutoRTL rejects `initial` blocks in RTL, and a generated child
  testbench compares every output from reset, so contents must be defined. The
  program is therefore loaded after reset while `run` is low; `run` is sampled
  only in F.
- `rf_we` is raised for every writing instruction including `rd = 0`; the
  register file drops writes to x0.
- Timing: an instruction takes F, D, E, W (4 cycles), a store adds M (5) and a
  load adds M and L (6); retire and the register write are visible in W, a store
  in M. Every child output is a view of registered state or a function of its
  inputs (combinational children), so no combinational loop exists.

## Implemented out of context

A core with a trace port is an SoC block. Its 151 port bits exceed the 106 user
I/O of xc7a35tcpg236-1, so `meta.yaml` sets `implementation: out_of_context`
(taxonomy `chip_top_flow_for_soc_block`; see docs/DESIGN.md "Implementation
flow"). Paths from ports to the first register are not timed in that flow.

## Independent testbench

`rv32i_core_tb.v` keeps its own pc, registers, data words and instruction image,
executes each instruction from the RV32I definition when the core fetches it,
commits at retirement, and checks `retire`, `rf_we` (with `rf_waddr` and
`rf_wdata` in W), `dmem_we` (with address and data in M) and `pc` before every
rising edge, which also fixes the cycle count of each instruction. Programs:
`alu` (every operation and immediate form, sign and shift corner cases, x0
writes, FENCE/ECALL), `fib` (20 Fibonacci numbers stored, then summed by a
load loop), `memcpy` (fill, copy with two pointers, negative offsets, address
aliasing, an unaligned address), `branch` (every branch taken and not taken
with signed/unsigned edge cases, the reserved encodings, JAL and JALR links, a
backward loop, a call and return); `branch` again with `run` randomly low; then
forty seeded random 64-word programs with forward-only control flow, half of
them with `run` randomly low, one aborted by a mid-program reset and two with
off-edge reset pulses. Each program starts with a reset of the busy core.
Stimulus never depends on DUT outputs.

## Qualification (run)

`qualification/reference.v` holds the six reference children and the mechanical
top (byte-identical to `top_verilog(spec)`); `qualification/mutants.json` has
ten single-site faults across the decoder, ALU, register file, both memories
and the sequencer.

```powershell
python curriculum/tier6/qualify_tier6.py curriculum/tier6/rv32i_core_build <absolute out dir>
```

Run in Vivado 2025.2 xsim (xvlog/xelab/xsim only; no synthesis). The reference
passes and every mutant fails with raw `FAIL BEHAVIOR` lines and no watchdog;
`qualification/qualification.json` and `qualification/console.txt` are the
recorded result. The testbench hash there is over the LF bytes as committed.
No synthesis, implementation or harness build of this entry has run.
