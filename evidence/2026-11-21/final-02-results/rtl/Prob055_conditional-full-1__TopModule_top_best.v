`timescale 1ns/1ps
// @latency 0
module TopModule_top (
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [7:0] c,
    input  wire [7:0] d,
    output wire [7:0] min
);

    wire [7:0] min_ab;
    wire [7:0] min_cd;

    // An unsigned pair minimum is at least 128 exactly when both operands are.
    assign min_ab[7]   = a[7] & b[7];
    assign min_ab[6:0] = (a < b) ? a[6:0] : b[6:0];

    assign min_cd[7]   = c[7] & d[7];
    assign min_cd[6:0] = (c < d) ? c[6:0] : d[6:0];

    assign min[7]   = min_ab[7] & min_cd[7];
    assign min[6:0] = (min_ab < min_cd) ? min_ab[6:0] : min_cd[6:0];

    // Manual checks against the unsigned minimum of all four inputs matched.
    // (0,1,128,255) -> 0, (128,127,130,131) -> 127
    // (255,254,128,129) -> 128, (140,141,131,130) -> 130
    // (80,81,81,80) -> 80, (255,255,255,255) -> 255
    // (43,254,42,255) -> 42

endmodule