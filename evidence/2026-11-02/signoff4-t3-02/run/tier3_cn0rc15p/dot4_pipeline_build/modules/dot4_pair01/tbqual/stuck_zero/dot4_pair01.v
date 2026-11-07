`timescale 1ns/1ps
// @latency 1
module dot4_pair01 (clk, rst, a0, b0, a1, b1, pair01_sum);
input wire clk;
input wire rst;
input wire [7:0] a0;
input wire [7:0] b0;
input wire [7:0] a1;
input wire [7:0] b1;
output wire [16:0] pair01_sum;
assign pair01_sum = 0;
endmodule
