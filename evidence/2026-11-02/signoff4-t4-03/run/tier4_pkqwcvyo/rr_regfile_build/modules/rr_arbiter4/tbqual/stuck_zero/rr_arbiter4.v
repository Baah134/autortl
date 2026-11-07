`timescale 1ns/1ps
// @latency 1
module rr_arbiter4 (clk, rst, req, addr0, data0, addr1, data1, addr2, data2, addr3, data3, grant, wr_en, wr_addr, wr_data);
input wire clk;
input wire rst;
input wire [3:0] req;
input wire [2:0] addr0;
input wire [7:0] data0;
input wire [2:0] addr1;
input wire [7:0] data1;
input wire [2:0] addr2;
input wire [7:0] data2;
input wire [2:0] addr3;
input wire [7:0] data3;
output wire [3:0] grant;
output wire wr_en;
output wire [2:0] wr_addr;
output wire [7:0] wr_data;
assign grant = 0;
assign wr_en = 0;
assign wr_addr = 0;
assign wr_data = 0;
endmodule
