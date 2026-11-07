`timescale 1ns/1ps
// @latency 1
module dot4_pair23 (
    input wire clk,
    input wire rst,
    input wire [7:0] a2,
    input wire [7:0] b2,
    input wire [7:0] a3,
    input wire [7:0] b3,
    output wire [16:0] pair23_sum
);

    wire [15:0] a2_ext = {8'b0, a2};
    wire [15:0] b2_ext = {8'b0, b2};
    wire [15:0] a3_ext = {8'b0, a3};
    wire [15:0] b3_ext = {8'b0, b3};

    wire [15:0] product2 = a2_ext * b2_ext;
    wire [15:0] product3 = a3_ext * b3_ext;
    wire [16:0] sum = {1'b0, product2} + {1'b0, product3};

    reg [16:0] pair23_sum_reg;
    assign pair23_sum = pair23_sum_reg;

    always @(posedge clk) begin
        if (rst)
            pair23_sum_reg <= 17'b0;
        else
            pair23_sum_reg <= sum;
    end

endmodule