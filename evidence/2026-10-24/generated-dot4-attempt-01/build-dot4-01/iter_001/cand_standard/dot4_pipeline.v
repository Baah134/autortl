`timescale 1ns/1ps
module dot4_pipeline (
    input wire clk,
    input wire rst,
    input wire [7:0] a0,
    input wire [7:0] b0,
    input wire [7:0] a1,
    input wire [7:0] b1,
    input wire [7:0] a2,
    input wire [7:0] b2,
    input wire [7:0] a3,
    input wire [7:0] b3,
    output wire [17:0] dot_result
);
    (* use_dsp = "yes" *) wire [15:0] product0 = a0 * b0;
    (* use_dsp = "yes" *) wire [15:0] product1 = a1 * b1;
    (* use_dsp = "yes" *) wire [15:0] product2 = a2 * b2;
    (* use_dsp = "yes" *) wire [15:0] product3 = a3 * b3;

    wire [16:0] sum01 = {1'b0, product0} + {1'b0, product1};
    wire [16:0] sum23 = {1'b0, product2} + {1'b0, product3};

    reg [16:0] pair01_sum_reg;
    reg [16:0] pair23_sum_reg;
    reg [17:0] dot_result_reg;

    assign dot_result = dot_result_reg;

    always @(posedge clk) begin
        if (rst) begin
            pair01_sum_reg <= 17'd0;
            pair23_sum_reg <= 17'd0;
            dot_result_reg <= 18'd0;
        end else begin
            pair01_sum_reg <= sum01;
            pair23_sum_reg <= sum23;
            dot_result_reg <= {1'b0, pair01_sum_reg} +
                              {1'b0, pair23_sum_reg};
        end
    end
endmodule