`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire a,
    input  wire b,
    input  wire c,
    input  wire d,
    output wire out
);
    wire [15:0] truth_table;
    assign truth_table = 16'h8BD7;
    assign out = truth_table[{a, b, c, d}];
endmodule