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

    reg [16:0] sum_q;

    always @(posedge clk) begin
        if (rst)
            sum_q <= 17'b0;
        else
            sum_q <= sum;
    end

    assign pair01_sum = sum_q;

endmodule