`timescale 1ns/1ps
module driver_prolonged_block(input clk,rst,input [7:0] a,input [4:0] b,
 input in_valid,out_ready,output in_ready,output reg out_valid,
 output reg [7:0] y,z);
reg [5:0] warm;
assign in_ready=(warm>=17) && (!out_valid || out_ready);
always @(posedge clk) begin
 if(rst) begin warm<=0;out_valid<=0;y<=0;z<=0;end
 else begin
  if(warm<17) warm<=warm+1'b1;
  if(in_ready) begin out_valid<=in_valid;if(in_valid) begin y<=a+b;z<=a^b;end end
 end
end
endmodule
