`timescale 1ns / 1ps
`default_nettype none
// Adapter: fir16_sym (harness winner, unedited; built by the harness for
// 150 MHz, run here in the shell's 100 MHz clock). The winner is a five-slot
// elastic valid/ready pipeline, so the adapter only maps ports.
// in_word  = signed 16-bit sample
// out_word = signed 16-bit rounded, saturated output
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
    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    fir16_sym u_winner (
        .clk(clk), .rst(rst),
        .in_sample(in_word), .in_valid(in_valid), .in_ready(in_ready),
        .out_sample(out_word), .out_valid(out_valid), .out_ready(out_ready)
    );
endmodule
`default_nettype wire
