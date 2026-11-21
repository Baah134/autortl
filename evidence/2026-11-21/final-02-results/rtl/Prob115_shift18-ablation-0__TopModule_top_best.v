`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire load,
    input wire ena,
    input wire [1:0] amount,
    input wire [63:0] data,
    output wire [63:0] q
);
    TopModule u_TopModule (
        .clk(clk),
        .load(load),
        .ena(ena),
        .amount(amount),
        .data(data),
        .q(q)
    );
endmodule
