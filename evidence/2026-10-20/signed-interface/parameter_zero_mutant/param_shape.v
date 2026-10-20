`timescale 1ns/1ps
module param_shape (a, y);
parameter W = 8;
parameter EXTRA = 0;
localparam PW = W + EXTRA;
input wire signed [PW - 1:0] a;
output wire signed [0:PW - 1] y;
assign y=0;
endmodule
