`timescale 1ns / 1ps
`default_nettype none
// Adapter: signed_fir4 (harness winner, unedited).
// in_word  = signed 8-bit sample x
// out_word = 13-bit signed y, sign-extended to 16 bits
module stream_dut (
    input  wire        clk,
    input  wire        rst,
    input  wire [7:0]  in_word,
    input  wire        in_valid,
    output wire        in_ready,
    output wire [15:0] out_word,
    output wire        out_valid,
    input  wire        out_ready
);
    wire signed [12:0] y;

    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    signed_fir4 u_winner (
        .clk(clk), .rst(rst),
        .x(in_word), .in_valid(in_valid), .in_ready(in_ready),
        .out_data(y), .out_valid(out_valid), .out_ready(out_ready)
    );

    assign out_word = {{3{y[12]}}, y};
endmodule
`default_nettype wire
