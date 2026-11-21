`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    output wire out
);
    TopModule u_TopModule (
        .out(out)
    );
endmodule
