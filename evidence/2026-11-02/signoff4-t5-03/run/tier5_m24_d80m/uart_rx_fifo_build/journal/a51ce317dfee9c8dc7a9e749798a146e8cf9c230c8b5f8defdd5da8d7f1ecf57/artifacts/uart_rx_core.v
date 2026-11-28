`timescale 1ns/1ps
// @latency 1
module uart_rx_core (clk, rst, rx, rx_data, rx_strobe, frame_err);
parameter OVERSAMPLE_DIV = 2;
input wire clk;
input wire rst;
input wire rx;
output wire [7:0] rx_data;
output wire rx_strobe;
output wire frame_err;
assign rx_data = 0;
assign rx_strobe = 0;
assign frame_err = 0;
endmodule
