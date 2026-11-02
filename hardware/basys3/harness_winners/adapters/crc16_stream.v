`timescale 1ns / 1ps
`default_nettype none
// Adapter: crc16_stream (harness winner, unedited). The winner is a one-slot
// valid/ready stage that emits one output per accepted byte (in_ready =
// !out_valid || out_ready), so one shell transaction is one winner transfer
// and the adapter only maps ports. Frames are formed by the last flag in the
// stimulus; like the FIR filters, the winner keeps its frame state across
// transactions and a restart clears it.
// in_word  byte 0 = in_data; byte 1 = the last marker, any nonzero value sets
//          in_last (as in the packet FIFO, so every input bit has a load)
// out_word bytes 0..1 = out_crc, byte 2 = {7'd0, out_last}
module stream_dut (
    input  wire        clk,
    input  wire        rst,
    input  wire [15:0] in_word,
    input  wire        in_valid,
    output wire        in_ready,
    output wire [23:0] out_word,
    output wire        out_valid,
    input  wire        out_ready
);
    wire [15:0] crc;
    wire        last;

    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    crc16_stream u_winner (
        .clk(clk), .rst(rst),
        .in_data(in_word[7:0]), .in_last(|in_word[15:8]),
        .in_valid(in_valid), .in_ready(in_ready),
        .out_crc(crc), .out_last(last),
        .out_valid(out_valid), .out_ready(out_ready)
    );

    assign out_word = {7'd0, last, crc};
endmodule
`default_nettype wire
