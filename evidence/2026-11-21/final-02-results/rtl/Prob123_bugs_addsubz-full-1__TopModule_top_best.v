`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire do_sub,
    input wire [7:0] a,
    input wire [7:0] b,
    output wire [7:0] out,
    output wire result_is_zero
);
    TopModule u_TopModule (
        .do_sub(do_sub),
        .a(a),
        .b(b),
        .out(out),
        .result_is_zero(result_is_zero)
    );
endmodule
