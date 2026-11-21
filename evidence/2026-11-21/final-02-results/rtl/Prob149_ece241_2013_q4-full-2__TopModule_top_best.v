`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire reset,
    input wire [2:0] s,
    output wire fr2,
    output wire fr1,
    output wire fr0,
    output wire dfr
);
    TopModule u_TopModule (
        .clk(clk),
        .reset(reset),
        .s(s),
        .fr2(fr2),
        .fr1(fr1),
        .fr0(fr0),
        .dfr(dfr)
    );
endmodule
