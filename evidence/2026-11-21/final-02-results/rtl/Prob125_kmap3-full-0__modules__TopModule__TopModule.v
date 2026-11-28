`timescale 1ns/1ps
// @latency 0
module TopModule (
    input wire a,
    input wire b,
    input wire c,
    input wire d,
    output wire out
);
    assign out = a | (c & ~b);
endmodule