`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire [15:0] in,
    output wire [7:0] out_hi,
    output wire [7:0] out_lo
);
    TopModule u_TopModule (
        .in(in),
        .out_hi(out_hi),
        .out_lo(out_lo)
    );
endmodule
