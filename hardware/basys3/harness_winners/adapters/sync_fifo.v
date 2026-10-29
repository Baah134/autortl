`timescale 1ns / 1ps
`default_nettype none
// Adapter: sync_fifo (harness winner, unedited). Identity on 8-bit words.
module stream_dut (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] in_word,
    input  wire       in_valid,
    output wire       in_ready,
    output wire [7:0] out_word,
    output wire       out_valid,
    input  wire       out_ready
);
    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    sync_fifo u_winner (
        .clk(clk), .rst(rst),
        .in_data(in_word), .in_valid(in_valid), .in_ready(in_ready),
        .out_data(out_word), .out_valid(out_valid), .out_ready(out_ready)
    );
endmodule
`default_nettype wire
