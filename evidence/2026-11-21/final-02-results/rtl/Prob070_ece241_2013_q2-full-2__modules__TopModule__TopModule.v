`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire a,
    input  wire b,
    input  wire c,
    input  wire d,
    output wire out_sop,
    output wire out_pos
);
    wire result;

    assign result = c & (d | (~a & ~b));
    assign out_sop = result;
    assign out_pos = result;
endmodule