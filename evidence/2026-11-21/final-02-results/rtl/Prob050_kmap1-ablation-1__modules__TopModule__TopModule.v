`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire a,
    input  wire b,
    input  wire c,
    output wire out
);

    assign out = a | b | c;

endmodule