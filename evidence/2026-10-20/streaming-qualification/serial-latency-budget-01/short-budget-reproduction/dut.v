`timescale 1ns/1ps
module stream_pair(input clk,rst,input [7:0] a,b,input in_valid,out_ready,
output in_ready,output reg out_valid,output reg [7:0] y,z);
reg busy; integer remaining;
assign in_ready=!busy && !out_valid;
always @(posedge clk) begin
 if(rst) begin busy<=0; remaining<=0; out_valid<=0;y<=0;z<=0;end
 else begin
  if(out_valid && out_ready) out_valid<=0;
  if(busy) begin
   if(remaining==1) begin busy<=0;out_valid<=1;end
   else remaining<=remaining-1;
  end
  if(in_valid && in_ready) begin busy<=1;remaining<=100;y<=a+b;z<=a^b;end
 end
end endmodule
