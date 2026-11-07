`timescale 1ns/1ps
module accumulated_cell(input clk, input rst, input [7:0] amount, output reg [7:0] total);
always @(posedge clk) begin
    if (rst) total <= 0;
    else total <= total + amount;
end
endmodule
