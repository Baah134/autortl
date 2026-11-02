`timescale 1ns/1ps
// @latency 0
module cordic_prerot (angle, x0, z0);
input wire [15:0] angle;
output wire [17:0] x0;
output wire [19:0] z0;
assign x0 = 0;
assign z0 = 0;
endmodule
