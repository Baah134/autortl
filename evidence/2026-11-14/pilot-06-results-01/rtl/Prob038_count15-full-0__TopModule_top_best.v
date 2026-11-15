`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire reset,
    output wire [3:0] q
);
    TopModule u_TopModule (
        .clk(clk),
        .reset(reset),
        .q(q)
    );
endmodule
