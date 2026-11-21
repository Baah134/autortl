`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire reset,
    input wire [31:0] in,
    output wire [31:0] out
);
    TopModule u_TopModule (
        .clk(clk),
        .reset(reset),
        .in(in),
        .out(out)
    );
endmodule
