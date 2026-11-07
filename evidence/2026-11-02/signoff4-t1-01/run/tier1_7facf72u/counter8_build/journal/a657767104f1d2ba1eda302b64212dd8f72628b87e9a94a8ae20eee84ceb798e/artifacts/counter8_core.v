`timescale 1ns/1ps
// @latency 1
module counter8_core (
    input wire clk,
    input wire rst,
    input wire enable,
    output wire [7:0] count
);

reg [7:0] count_reg;

assign count = count_reg;

always @(posedge clk) begin
    if (rst)
        count_reg <= 8'b0;
    else if (enable)
        count_reg <= count_reg + 8'b1;
end

endmodule