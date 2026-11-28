`timescale 1ns/1ps
// @latency 1
module uart_tx (clk, rst, data, tx);
parameter DIV = 868;
input wire clk;
input wire rst;
input wire [7:0] data;
output wire tx;
assign tx = -1;
endmodule
