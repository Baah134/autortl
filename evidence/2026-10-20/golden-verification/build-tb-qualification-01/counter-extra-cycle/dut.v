`timescale 1ns/1ps
module counter8(input clk,rst,enable,output reg [7:0] count);
reg [7:0] state;
always @(posedge clk) begin
    if (rst) begin state<=0; count<=0; end
    else begin
        if (enable) state<=state+1'b1;
        count<=state;
    end
end
endmodule
