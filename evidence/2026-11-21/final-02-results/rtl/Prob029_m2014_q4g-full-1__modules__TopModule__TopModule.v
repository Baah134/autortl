`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire in1,
    input  wire in2,
    input  wire in3,
    output wire out
);
    assign out = ~^{in3, in2, in1};
endmodule