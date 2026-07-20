---
name: xilinx-inference
description: "Use when the design involves multiplication, MAC, filters, memories, RAM, buffers, or large shift registers — coding patterns that make Vivado infer DSP48, BRAM, and SRL primitives."
---
# Xilinx 7-Series Inference Patterns

## DSP48 (multiply / MAC)
Write the multiply plainly and REGISTER inputs and outputs; Vivado maps to DSP48E1 with internal pipeline registers:
```verilog
always @(posedge clk) begin
    a_r <= a;  b_r <= b;        // input regs
    p   <= a_r * b_r;           // maps into DSP48
    acc <= acc + p;             // post-adder can also absorb into DSP
end
```
Signed math: declare `signed` and let the tool handle it. Avoid slicing the product before registering it.

## Block RAM
```verilog
(* ram_style = "block" *) reg [DW-1:0] mem [0:DEPTH-1];
always @(posedge clk) begin
    if (we) mem[waddr] <= wdata;
    rdata <= mem[raddr];        // registered read REQUIRED for BRAM
end
```
Asynchronous reads force distributed RAM (LUTs). Depth >= 512 or width*depth >= ~18Kb favours BRAM.

## SRL (shift registers)
An N-deep shift register with no reset and no parallel taps maps into SRL16/SRL32 LUTs — do NOT reset delay-line registers.

## Carry chains
`a + b` and comparisons use dedicated carry logic — never hand-build adders. Prefer one wide add over several narrow chained ones on the critical path.
