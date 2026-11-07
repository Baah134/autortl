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

    wire [15:0] a0_ext = {8'b0, a0};
    wire [15:0] b0_ext = {8'b0, b0};
    wire [15:0] a1_ext = {8'b0, a1};
    wire [15:0] b1_ext = {8'b0, b1};

    wire [15:0] product0 = a0_ext * b0_ext;
    wire [15:0] product1 = a1_ext * b1_ext;
    wire [16:0] sum_comb = {1'b0, product0} + {1'b0, product1};

    reg [16:0] sum_reg;
    assign pair01_sum = sum_reg;

    always @(posedge clk) begin
        if (rst)
            sum_reg <= 17'b0;
        else
            sum_reg <= sum_comb;
    end

endmodule