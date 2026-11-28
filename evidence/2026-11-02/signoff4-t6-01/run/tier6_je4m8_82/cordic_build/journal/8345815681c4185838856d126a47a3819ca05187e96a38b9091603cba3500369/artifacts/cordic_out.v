`timescale 1ns/1ps
// @latency 0
module cordic_out (x_in, y_in, cos_out, sin_out);
input wire [17:0] x_in;
input wire [17:0] y_in;
output wire [15:0] cos_out;
output wire [15:0] sin_out;
assign cos_out = 0;
assign sin_out = 0;
endmodule
