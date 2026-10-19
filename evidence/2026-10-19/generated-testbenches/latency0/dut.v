`timescale 1ns/1ps
module latency0(input [7:0] a,b, output [7:0] y,z); assign y=a+b; assign z=a^b; endmodule