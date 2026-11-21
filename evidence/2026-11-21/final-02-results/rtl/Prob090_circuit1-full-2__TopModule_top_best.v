`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire a,
    input wire b,
    output wire q
);
    TopModule u_TopModule (
        .a(a),
        .b(b),
        .q(q)
    );
endmodule
