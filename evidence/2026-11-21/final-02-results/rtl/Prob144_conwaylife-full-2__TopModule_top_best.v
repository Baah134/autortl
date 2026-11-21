`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire load,
    input wire [255:0] data,
    output wire [255:0] q
);
    TopModule u_TopModule (
        .clk(clk),
        .load(load),
        .data(data),
        .q(q)
    );
endmodule
