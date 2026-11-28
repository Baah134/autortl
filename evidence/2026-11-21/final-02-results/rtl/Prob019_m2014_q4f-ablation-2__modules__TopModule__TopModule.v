`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire in1,
    input  wire in2,
    output wire out
);

    assign out = in1 & ~in2;

endmodule