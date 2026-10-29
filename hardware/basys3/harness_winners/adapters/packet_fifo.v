`timescale 1ns / 1ps
`default_nettype none
// Adapter: packet_fifo (harness winner, unedited).
// in_word  byte 0 = data, byte 1 = last marker (any nonzero value sets last)
// out_word byte 0 = data, byte 1 = {7'b0, last}
module stream_dut (
    input  wire        clk,
    input  wire        rst,
    input  wire [15:0] in_word,
    input  wire        in_valid,
    output wire        in_ready,
    output wire [15:0] out_word,
    output wire        out_valid,
    input  wire        out_ready
);
    wire [7:0] data;
    wire       last;

    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    packet_fifo u_winner (
        .clk(clk), .rst(rst),
        .in_data(in_word[7:0]), .in_last(|in_word[15:8]),
        .in_valid(in_valid), .in_ready(in_ready),
        .out_data(data), .out_last(last),
        .out_valid(out_valid), .out_ready(out_ready)
    );

    assign out_word = {7'd0, last, data};
endmodule
`default_nettype wire
