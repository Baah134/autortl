`timescale 1ns/1ps
// @latency 1
module dot4_pair01 (
    input wire clk,
    input wire rst,
    input wire [7:0] a0,
    input wire [7:0] b0,
    input wire [7:0] a1,
    input wire [7:0] b1,
    output wire [16:0] pair01_sum
);

    wire [15:0] product0 = a0 * b0;
    wire [15:0] product1 = a1 * b1;
    wire [16:0] sum = {1'b0, product0} + {1'b0, product1};

    reg [16:0] pair01_sum_reg;

    assign pair01_sum = pair01_sum_reg;

    always @(posedge clk) begin
        if (rst)
            pair01_sum_reg <= 17'd0;
        else
            pair01_sum_reg <= sum;
    end

endmodule