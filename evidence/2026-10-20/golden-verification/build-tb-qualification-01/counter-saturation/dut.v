`timescale 1ns/1ps
module counter8(input clk, rst, enable, output reg [7:0] count);
always @(posedge clk) begin
    if (rst) count <= 0;
    else if (enable) count <= (count == 8'hff) ? count : count + 1'b1;
end
endmodule
