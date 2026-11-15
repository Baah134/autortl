`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire a,
    input wire b,
    output wire q,
    output wire state
);
    TopModule u_TopModule (
        .clk(clk),
        .a(a),
        .b(b),
        .q(q),
        .state(state)
    );
endmodule
