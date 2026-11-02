`timescale 1ns/1ps
// @latency 1
module sync_fifo (clk, rst, in_valid, in_ready, in_data, out_valid, out_ready, out_data);
input wire clk;
input wire rst;
input wire in_valid;
output wire in_ready;
input wire [7:0] in_data;
output wire out_valid;
input wire out_ready;
output wire [7:0] out_data;
assign in_ready = 0;
assign out_valid = 0;
assign out_data = 0;
endmodule
