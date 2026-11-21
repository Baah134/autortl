`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire reset,
    input wire in,
    output wire done
);
    TopModule u_TopModule (
        .clk(clk),
        .reset(reset),
        .in(in),
        .done(done)
    );
endmodule
