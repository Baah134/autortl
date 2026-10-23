`timescale 1ns/1ps
// @latency 1
// Intentionally false annotation: temporal assertions must establish behavior.
module packet_fifo_core #(parameter WIDTH=8, parameter DEPTH=3)(
    input clk, input rst, input [WIDTH-1:0] in_data, input in_last,
    input in_valid, output in_ready, output [WIDTH-1:0] out_data,
    output out_last, output out_valid, input out_ready);
    assign in_ready = out_ready && !rst;
    assign out_valid = in_valid && !rst;
    assign out_data = in_data;
    assign out_last = in_last;
endmodule
