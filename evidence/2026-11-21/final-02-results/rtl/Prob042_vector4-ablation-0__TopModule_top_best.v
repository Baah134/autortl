`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire [7:0] in,
    output wire [31:0] out
);
    TopModule u_TopModule (
        .in(in),
        .out(out)
    );
endmodule
