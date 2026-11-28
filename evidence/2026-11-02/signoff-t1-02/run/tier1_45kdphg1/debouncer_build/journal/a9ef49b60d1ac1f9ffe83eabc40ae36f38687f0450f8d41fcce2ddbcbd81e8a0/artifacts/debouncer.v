`timescale 1ns/1ps
// @latency 0
module debouncer (clk, rst, noisy, clean);
input wire clk;
input wire rst;
input wire noisy;
output wire clean;
assign clean = -1;
endmodule
