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
    wire select_a;
    wire select_c;
    wire select_ab;

    assign select_a  = a < b;
    assign select_c  = c < d;
    assign select_ab = min_ab < min_cd;

    // Each pair uses four data bits and a shared select, so its two
    // mux functions can share a dual-output LUT. Physical packing is unverified.
    genvar pair;
    generate
        for (pair = 0; pair < 4; pair = pair + 1) begin : mux_pairs
            assign min_ab[2*pair +: 2] =
                select_a ? a[2*pair +: 2] : b[2*pair +: 2];
            assign min_cd[2*pair +: 2] =
                select_c ? c[2*pair +: 2] : d[2*pair +: 2];
            assign min[2*pair +: 2] =
                select_ab ? min_ab[2*pair +: 2] : min_cd[2*pair +: 2];
        end
    endgenerate

    // Manual comparison with the unsigned minimum found no counterexamples.
    // (0,128,254,255) -> 0, (128,127,254,255) -> 127
    // (255,254,127,128) -> 127, (255,254,128,127) -> 127
    // (255,255,255,255) -> 255, (128,128,255,255) -> 128
endmodule