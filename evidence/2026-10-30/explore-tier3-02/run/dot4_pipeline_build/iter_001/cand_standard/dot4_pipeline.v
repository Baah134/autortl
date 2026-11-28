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

    wire [16:0] sum01_next = {1'b0, product0} + {1'b0, product1};
    wire [16:0] sum23_next = {1'b0, product2} + {1'b0, product3};

    reg [16:0] sum01_reg;
    reg [16:0] sum23_reg;

    always @(posedge clk) begin
        if (rst) begin
            sum01_reg <= 17'd0;
            sum23_reg <= 17'd0;
        end else begin
            sum01_reg <= sum01_next;
            sum23_reg <= sum23_next;
        end
    end

    dot4_merge u_dot4_merge (
        .clk(clk),
        .rst(rst),
        .left_sum(sum01_reg),
        .right_sum(sum23_reg),
        .dot_result(dot_result)
    );
endmodule