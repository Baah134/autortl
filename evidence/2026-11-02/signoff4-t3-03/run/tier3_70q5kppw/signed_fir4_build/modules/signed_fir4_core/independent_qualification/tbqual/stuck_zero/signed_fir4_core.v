`timescale 1ns/1ps
// @latency 3
module signed_fir4_core (clk, rst, x, in_valid, in_ready, out_data, out_valid, out_ready);
input wire clk;
input wire rst;
input wire signed [7:0] x;
input wire in_valid;
output wire in_ready;
output wire signed [12:0] out_data;
output wire out_valid;
input wire out_ready;
assign in_ready = 0;
assign out_data = 0;
assign out_valid = 0;
endmodule
