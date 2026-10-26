`timescale 1ns/1ps
module driver_busy_sequential(input clk,rst,input [7:0] a,input [4:0] b,
 input in_valid,out_ready,output in_ready,output reg out_valid,
 output reg [7:0] y,z);
reg [1:0] busy;
assign in_ready=(busy==0) && (!out_valid || out_ready);
always @(posedge clk) begin
 if(rst) begin busy<=0;out_valid<=0;y<=0;z<=0;end
 else begin
  if(out_valid && out_ready) out_valid<=0;
  if(busy!=0) begin busy<=busy-1'b1;if(busy==1) out_valid<=1;end
  if(in_valid && in_ready) begin busy<=3;out_valid<=0;y<=a+b;z<=a^b;end
 end
end
endmodule
