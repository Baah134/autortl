`timescale 1ns/1ps
// @latency 1
module fir8 (
    input  wire               clk,
    input  wire               rst,
    input  wire signed [15:0] x_in,
    output reg  signed [31:0] y_out
);
    parameter signed [15:0] C0=16'd3, C1=16'd7, C2=16'd12, C3=16'd18,
                            C4=16'd18, C5=16'd12, C6=16'd7,  C7=16'd3;

    reg signed [15:0] x_d;
    reg signed [31:0] acc1, acc2, acc3, acc4, acc5, acc6, acc7;

    wire signed [31:0] p0 = x_d * C0;
    wire signed [31:0] p1 = x_d * C1;
    wire signed [31:0] p2 = x_d * C2;
    wire signed [31:0] p3 = x_d * C3;
    wire signed [31:0] p4 = x_d * C4;
    wire signed [31:0] p5 = x_d * C5;
    wire signed [31:0] p6 = x_d * C6;
    wire signed [31:0] p7 = x_d * C7;

    always @(posedge clk) begin
        if (rst) begin
            x_d   <= 16'sd0;
            acc1  <= 32'sd0;
            acc2  <= 32'sd0;
            acc3  <= 32'sd0;
            acc4  <= 32'sd0;
            acc5  <= 32'sd0;
            acc6  <= 32'sd0;
            acc7  <= 32'sd0;
            y_out <= 32'sd0;
        end else begin
            x_d   <= x_in;
            acc7  <= p7;
            acc6  <= p6 + acc7;
            acc5  <= p5 + acc6;
            acc4  <= p4 + acc5;
            acc3  <= p3 + acc4;
            acc2  <= p2 + acc3;
            acc1  <= p1 + acc2;
            y_out <= p0 + acc1;
        end
    end
endmodule