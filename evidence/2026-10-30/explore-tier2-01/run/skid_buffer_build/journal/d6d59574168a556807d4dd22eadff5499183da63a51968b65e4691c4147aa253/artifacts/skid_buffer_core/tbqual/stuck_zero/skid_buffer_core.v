`timescale 1ns/1ps
// @latency 1
module skid_buffer_core (clk, rst, in_data, in_valid, in_ready, out_data, out_valid, out_ready);
input wire clk;
input wire rst;
input wire [7:0] in_data;
input wire in_valid;
output wire in_ready;
output wire [7:0] out_data;
output wire out_valid;
input wire out_ready;
assign in_ready = 0;
assign out_data = 0;
assign out_valid = 0;
endmodule
