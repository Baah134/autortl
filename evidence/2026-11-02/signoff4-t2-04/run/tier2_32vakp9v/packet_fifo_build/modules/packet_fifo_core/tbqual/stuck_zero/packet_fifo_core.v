`timescale 1ns/1ps
// @latency 1
module packet_fifo_core (clk, rst, in_data, in_last, in_valid, in_ready, out_data, out_last, out_valid, out_ready);
parameter WIDTH = 8;
parameter DEPTH = 3;
input wire clk;
input wire rst;
input wire [WIDTH - 1:0] in_data;
input wire in_last;
input wire in_valid;
output wire in_ready;
output wire [WIDTH - 1:0] out_data;
output wire out_last;
output wire out_valid;
input wire out_ready;
assign in_ready = 0;
assign out_data = 0;
assign out_last = 0;
assign out_valid = 0;
endmodule
