`timescale 1ns/1ps
module accumulated_cell(input clk, input rst, input [7:0] amount, output [7:0] total);
assign total = amount;
endmodule
