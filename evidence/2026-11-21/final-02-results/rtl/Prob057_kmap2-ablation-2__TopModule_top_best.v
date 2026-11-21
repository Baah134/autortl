`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire a,
    input wire b,
    input wire c,
    input wire d,
    output wire out
);
    TopModule u_TopModule (
        .a(a),
        .b(b),
        .c(c),
        .d(d),
        .out(out)
    );
endmodule
