`timescale 1ns / 1ps
`default_nettype none
// Adapter: elastic_dot4 (harness winner, unedited).
// in_word  bytes 0..7 = a0, b0, a1, b1, a2, b2, a3, b3 (unsigned)
// out_word = 18-bit unsigned dot product, zero-extended to 24 bits
module stream_dut (
    input  wire        clk,
    input  wire        rst,
    input  wire [63:0] in_word,
    input  wire        in_valid,
    output wire        in_ready,
    output wire [23:0] out_word,
    output wire        out_valid,
    input  wire        out_ready
);
    wire [17:0] dot;

    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    elastic_dot4 u_winner (
        .clk(clk), .rst(rst),
        .a0(in_word[7:0]),   .b0(in_word[15:8]),
        .a1(in_word[23:16]), .b1(in_word[31:24]),
        .a2(in_word[39:32]), .b2(in_word[47:40]),
        .a3(in_word[55:48]), .b3(in_word[63:56]),
        .in_valid(in_valid), .in_ready(in_ready),
        .out_data(dot), .out_valid(out_valid), .out_ready(out_ready)
    );

    assign out_word = {6'd0, dot};
endmodule
`default_nettype wire
