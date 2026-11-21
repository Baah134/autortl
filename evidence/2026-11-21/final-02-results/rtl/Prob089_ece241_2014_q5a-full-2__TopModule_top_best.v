`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire areset,
    input wire x,
    output wire z
);
    TopModule u_TopModule (
        .clk(clk),
        .areset(areset),
        .x(x),
        .z(z)
    );
endmodule
