`timescale 1ns/1ps
// @latency 0
module TopModule (
    input wire a,
    input wire b,
    output wire q
);
    assign q = a & b;
endmodule