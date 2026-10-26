`timescale 1ns/1ps
module driver_forward_zero(input clk,rst,input [7:0] a,input [4:0] b,
 input in_valid,out_ready,output in_ready,output wire out_valid,
 output wire [7:0] y,z);
assign in_ready=out_ready; assign out_valid=in_valid; assign y=a+b; assign z=a^b;
endmodule
