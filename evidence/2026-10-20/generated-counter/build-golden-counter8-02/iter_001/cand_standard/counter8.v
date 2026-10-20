`timescale 1ns/1ps
module counter8 (
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
        else
            count_reg <= count_reg + {7'b0, enable};
    end
endmodule