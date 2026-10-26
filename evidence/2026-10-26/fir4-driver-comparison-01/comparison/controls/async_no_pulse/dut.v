`timescale 1ns/1ps
module driver_async_no_pulse(input clk,rst,input [7:0] a,input [4:0] b,
 input in_valid,out_ready,output in_ready,output reg out_valid,
 output reg [7:0] y,z);
assign in_ready=(!out_valid || out_ready);
always @(posedge clk or posedge rst) begin
 if(rst) begin out_valid<=0;y<=0;z<=0;end
 else begin
  
  if(in_ready) begin out_valid<=in_valid;if(in_valid) begin y<=a+b;z<=a^b;end end
 end
end
endmodule
