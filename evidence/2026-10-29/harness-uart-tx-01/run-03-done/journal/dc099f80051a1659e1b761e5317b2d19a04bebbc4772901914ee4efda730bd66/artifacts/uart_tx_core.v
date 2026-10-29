`timescale 1ns/1ps
// @latency 1
module uart_tx_core (clk, rst, in_data, in_valid, in_ready, tx);
parameter integer DIV = 868;
input wire clk;
input wire rst;
input wire [7:0] in_data;
input wire in_valid;
output wire in_ready;
output wire tx;
assign in_ready = 0;
assign tx = 0;
endmodule
