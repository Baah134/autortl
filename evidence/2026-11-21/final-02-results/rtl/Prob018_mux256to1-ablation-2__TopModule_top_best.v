`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire [255:0] in,
    input wire [7:0] sel,
    output wire out
);
    TopModule u_TopModule (
        .in(in),
        .sel(sel),
        .out(out)
    );
endmodule
