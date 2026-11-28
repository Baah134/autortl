`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire j,
    input wire k,
    output wire Q
);
    TopModule u_TopModule (
        .clk(clk),
        .j(j),
        .k(k),
        .Q(Q)
    );
endmodule
