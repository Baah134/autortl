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

    wire [15:0] product2;
    wire [15:0] product3;
    wire [16:0] sum_next;
    reg [16:0] pair23_sum_reg;

    assign product2 = a2 * b2;
    assign product3 = a3 * b3;
    assign sum_next = {1'b0, product2} + {1'b0, product3};
    assign pair23_sum = pair23_sum_reg;

    always @(posedge clk) begin
        if (rst)
            pair23_sum_reg <= 17'd0;
        else
            pair23_sum_reg <= sum_next;
    end

endmodule