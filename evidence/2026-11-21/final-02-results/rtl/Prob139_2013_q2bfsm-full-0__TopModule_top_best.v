`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire resetn,
    input wire x,
    input wire y,
    output wire f,
    output wire g
);
    TopModule u_TopModule (
        .clk(clk),
        .resetn(resetn),
        .x(x),
        .y(y),
        .f(f),
        .g(g)
    );
endmodule
