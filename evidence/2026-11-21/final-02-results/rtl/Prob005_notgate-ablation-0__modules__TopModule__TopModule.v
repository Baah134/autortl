`timescale 1ns/1ps
// @latency 0
module TopModule (
    input wire in,
    output wire out
);
    assign out = ~in;
endmodule