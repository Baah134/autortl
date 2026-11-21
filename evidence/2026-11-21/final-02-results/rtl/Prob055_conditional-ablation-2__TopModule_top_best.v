`timescale 1ns/1ps
// @latency 0
module TopModule_top (
    input wire [7:0] a,
    input wire [7:0] b,
    input wire [7:0] c,
    input wire [7:0] d,
    output wire [7:0] min
);
    wire [7:0] min_ab;
    wire [7:0] min_cd;

    assign min_ab[6:0] = (a < b) ? a[6:0] : b[6:0];
    assign min_ab[7]   = a[7] & b[7];

    assign min_cd[6:0] = (c < d) ? c[6:0] : d[6:0];
    assign min_cd[7]   = c[7] & d[7];

    assign min[6:0] = (min_ab < min_cd) ? min_ab[6:0] : min_cd[6:0];
    assign min[7]   = min_ab[7] & min_cd[7];

    // Hand-checked against the smallest unsigned input.
    // a  b  c  d    min (hex)
    // 00 00 00 00    00
    // FF FF FF FF    FF
    // 7F 80 FF FF    7F
    // FF FF 80 7F    7F
    // 7F FF 80 FF    7F
    // The last three vectors each give 00 if the comparison at the
    // respective a/b, c/d, or final node is signed or omits bit 7.
endmodule