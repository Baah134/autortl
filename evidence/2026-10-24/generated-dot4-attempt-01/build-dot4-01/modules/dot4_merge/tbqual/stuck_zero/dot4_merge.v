`timescale 1ns/1ps
// @latency 1
module dot4_merge (clk, rst, left_sum, right_sum, dot_result);
input wire clk;
input wire rst;
input wire [16:0] left_sum;
input wire [16:0] right_sum;
output wire [17:0] dot_result;
assign dot_result = 0;
endmodule
