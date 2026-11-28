`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire [2:0] y,
    input wire w,
    output wire Y1
);
    TopModule u_TopModule (
        .y(y),
        .w(w),
        .Y1(Y1)
    );
endmodule
