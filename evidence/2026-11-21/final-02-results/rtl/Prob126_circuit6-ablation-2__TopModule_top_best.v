`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire [2:0] a,
    output wire [15:0] q
);
    TopModule u_TopModule (
        .a(a),
        .q(q)
    );
endmodule
