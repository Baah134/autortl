`timescale 1ns/1ps
module stream_pair(input clk,rst,input [7:0] a,b,input in_valid,out_ready,
output in_ready,out_valid,output [7:0] y,z);
assign in_ready=out_ready && !rst;
assign out_valid=in_valid && !rst;
assign y=a+b; assign z=a^b; endmodule
