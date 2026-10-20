`timescale 1ns/1ps
module priority_encoder8_core (clk, rst, request, index, valid);
input wire clk;
input wire rst;
input wire [7:0] request;
output wire [2:0] index;
output wire valid;
assign index = 0;
assign valid = 0;
endmodule
