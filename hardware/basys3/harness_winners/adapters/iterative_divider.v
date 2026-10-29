`timescale 1ns / 1ps
`default_nettype none
// Adapter: iterative_divider (harness winner, unedited).
// in_word  byte 0 = dividend, byte 1 = divisor (unsigned)
// out_word byte 0 = quotient, byte 1 = remainder
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
    wire [7:0] quotient, remainder;

    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    iterative_divider u_winner (
        .clk(clk), .rst(rst),
        .dividend(in_word[7:0]), .divisor(in_word[15:8]),
        .in_valid(in_valid), .in_ready(in_ready),
        .quotient(quotient), .remainder(remainder),
        .out_valid(out_valid), .out_ready(out_ready)
    );

    assign out_word = {remainder, quotient};
endmodule
`default_nettype wire
