`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire in1,
    input wire in2,
    output wire out
);
    TopModule u_TopModule (
        .in1(in1),
        .in2(in2),
        .out(out)
    );
endmodule
