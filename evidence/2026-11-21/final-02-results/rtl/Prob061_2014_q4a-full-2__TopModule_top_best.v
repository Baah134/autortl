`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire w,
    input wire R,
    input wire E,
    input wire L,
    output wire Q
);
    TopModule u_TopModule (
        .clk(clk),
        .w(w),
        .R(R),
        .E(E),
        .L(L),
        .Q(Q)
    );
endmodule
