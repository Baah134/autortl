`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire in,
    output wire out
);
    TopModule u_TopModule (
        .in(in),
        .out(out)
    );
endmodule
