`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire c,
    input wire d,
    output wire [3:0] mux_in
);
    TopModule u_TopModule (
        .c(c),
        .d(d),
        .mux_in(mux_in)
    );
endmodule
