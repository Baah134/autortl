`timescale 1ns/1ps
// @latency 0
module aes_key_step (key_in, rcon, key_out);
input wire [127:0] key_in;
input wire [7:0] rcon;
output wire [127:0] key_out;
assign key_out = 0;
endmodule
