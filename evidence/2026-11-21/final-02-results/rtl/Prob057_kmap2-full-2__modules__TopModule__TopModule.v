`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire a,
    input  wire b,
    input  wire c,
    input  wire d,
    output wire out
);
    localparam [15:0] TRUTH_TABLE = 16'h8BD7;
    wire [3:0] index;

    assign index = {a, b, c, d};
    assign out = TRUTH_TABLE[index];
endmodule