`timescale 1ns / 1ps
`default_nettype none
// Adapter: cordic_sincos (harness winner, unedited). The winner has its own
// valid/ready handshake (in_ready only while idle with no result pending),
// so the adapter only maps ports.
// in_word  = 16-bit binary angle (one turn = 2^16)
// out_word = {cos_out, sin_out}: bytes 0..1 = sin_out, bytes 2..3 = cos_out (Q2.14)
module stream_dut (
    input  wire        clk,
    input  wire        rst,
    input  wire [15:0] in_word,
    input  wire        in_valid,
    output wire        in_ready,
    output wire [31:0] out_word,
    output wire        out_valid,
    input  wire        out_ready
);
    wire [15:0] cos_out, sin_out;

    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    cordic_sincos u_winner (
        .clk(clk), .rst(rst),
        .angle(in_word), .in_valid(in_valid), .in_ready(in_ready),
        .out_valid(out_valid), .out_ready(out_ready),
        .cos_out(cos_out), .sin_out(sin_out)
    );

    assign out_word = {cos_out, sin_out};
endmodule
`default_nettype wire
