`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire [2:0] vec,
    output wire [2:0] outv,
    output wire o2,
    output wire o1,
    output wire o0
);
    TopModule u_TopModule (
        .vec(vec),
        .outv(outv),
        .o2(o2),
        .o1(o1),
        .o0(o0)
    );
endmodule
