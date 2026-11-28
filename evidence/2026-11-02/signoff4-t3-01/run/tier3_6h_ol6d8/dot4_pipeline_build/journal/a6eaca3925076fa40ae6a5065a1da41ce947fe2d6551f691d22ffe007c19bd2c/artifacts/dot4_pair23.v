`timescale 1ns/1ps
// @latency 1
module dot4_pair23 (clk, rst, a2, b2, a3, b3, pair23_sum);
input wire clk;
input wire rst;
input wire [7:0] a2;
input wire [7:0] b2;
input wire [7:0] a3;
input wire [7:0] b3;
output wire [16:0] pair23_sum;
assign pair23_sum = 0;
endmodule
