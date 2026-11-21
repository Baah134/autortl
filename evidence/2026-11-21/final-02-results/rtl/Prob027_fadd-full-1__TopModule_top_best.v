`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire a,
    input wire b,
    input wire cin,
    output wire cout,
    output wire sum
);
    TopModule u_TopModule (
        .a(a),
        .b(b),
        .cin(cin),
        .cout(cout),
        .sum(sum)
    );
endmodule
