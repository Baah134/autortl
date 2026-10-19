`timescale 1ns/1ps
module latency3(input clk,rst, input [7:0] a,b, output [7:0] y,z);
reg [7:0] py[0:2], pz[0:2]; integer i;
assign y=py[2]; assign z=pz[2];
always @(posedge clk) begin
 if(rst) begin for(i=0;i<3;i=i+1) begin py[i]<=0; pz[i]<=0; end end
 else begin py[0]<=a+b; pz[0]<=a^b;
 for(i=1;i<3;i=i+1) begin py[i]<=py[i-1]; pz[i]<=pz[i-1]; end end
end endmodule