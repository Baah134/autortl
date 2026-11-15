`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire ring,
    input wire vibrate_mode,
    output wire ringer,
    output wire motor
);
    TopModule u_TopModule (
        .ring(ring),
        .vibrate_mode(vibrate_mode),
        .ringer(ringer),
        .motor(motor)
    );
endmodule
