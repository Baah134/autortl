`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire a,
    input wire b,
    input wire c,
    output wire w,
    output wire x,
    output wire y,
    output wire z
);
    TopModule u_TopModule (
        .a(a),
        .b(b),
        .c(c),
        .w(w),
        .x(x),
        .y(y),
        .z(z)
    );
endmodule
