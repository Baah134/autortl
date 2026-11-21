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

    assign out_sop = (~a & ~b & c) | (b & c & d);
    assign out_pos = c & (~a | b) & (~b | d);

endmodule