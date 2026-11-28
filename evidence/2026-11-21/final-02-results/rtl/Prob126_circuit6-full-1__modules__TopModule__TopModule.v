`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire [2:0]  a,
    output wire [15:0] q
);

    // Bit n of each truth table is the output at address n.
    // All functions share the same three inputs for dual-output LUT packing.
    localparam [7:0] BIT_0  = 8'h80;
    localparam [7:0] BIT_1  = 8'h79;
    localparam [7:0] BIT_2  = 8'h7C;
    localparam [7:0] BIT_3  = 8'hA8;
    localparam [7:0] BIT_4  = 8'h85;
    localparam [7:0] BIT_5  = 8'h53;
    localparam [7:0] BIT_6  = 8'h36;
    localparam [7:0] BIT_7  = 8'h26;
    localparam [7:0] BIT_8  = 8'hC4;
    localparam [7:0] BIT_9  = 8'h8F;
    localparam [7:0] BIT_10 = 8'hE6;
    localparam [7:0] BIT_11 = 8'h8A;
    localparam [7:0] BIT_12 = 8'h09;
    localparam [7:0] BIT_13 = 8'hB6;
    localparam [7:0] BIT_14 = 8'h68;
    localparam [7:0] BIT_15 = 8'h42;

    assign q = {
        BIT_15[a], BIT_14[a], BIT_13[a], BIT_12[a],
        BIT_11[a], BIT_10[a], BIT_9[a],  BIT_8[a],
        BIT_7[a],  BIT_6[a],  BIT_5[a],  BIT_4[a],
        BIT_3[a],  BIT_2[a],  BIT_1[a],  BIT_0[a]
    };

endmodule