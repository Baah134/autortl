`timescale 1ns/1ps
module driver_renamed_active_low(input clk,reset_n,input [7:0] a,input [4:0] b,
 input request_valid,response_ready,output request_ready,output reg response_valid,
 output reg [7:0] y,z);
assign request_ready=(!response_valid || response_ready);
always @(posedge clk) begin
 if(!reset_n) begin response_valid<=0;y<=0;z<=0;end
 else begin
  
  if(request_ready) begin response_valid<=request_valid;if(request_valid) begin y<=a+b;z<=a^b;end end
 end
end
endmodule
