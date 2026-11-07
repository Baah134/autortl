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

    wire signed [31:0] p0 = {{16{x_d[15]}}, x_d} * {{16{C0[15]}}, C0};
    wire signed [31:0] p1 = {{16{x_d[15]}}, x_d} * {{16{C1[15]}}, C1};
    wire signed [31:0] p2 = {{16{x_d[15]}}, x_d} * {{16{C2[15]}}, C2};
    wire signed [31:0] p3 = {{16{x_d[15]}}, x_d} * {{16{C3[15]}}, C3};
    wire signed [31:0] p4 = {{16{x_d[15]}}, x_d} * {{16{C4[15]}}, C4};
    wire signed [31:0] p5 = {{16{x_d[15]}}, x_d} * {{16{C5[15]}}, C5};
    wire signed [31:0] p6 = {{16{x_d[15]}}, x_d} * {{16{C6[15]}}, C6};
    wire signed [31:0] p7 = {{16{x_d[15]}}, x_d} * {{16{C7[15]}}, C7};

    (* use_dsp = "no" *) wire signed [31:0] sum6 = p6 + acc7;
    (* use_dsp = "no" *) wire signed [31:0] sum5 = p5 + acc6;
    (* use_dsp = "no" *) wire signed [31:0] sum4 = p4 + acc5;
    (* use_dsp = "no" *) wire signed [31:0] sum3 = p3 + acc4;
    (* use_dsp = "no" *) wire signed [31:0] sum2 = p2 + acc3;
    (* use_dsp = "no" *) wire signed [31:0] sum1 = p1 + acc2;
    (* use_dsp = "no" *) wire signed [31:0] sum0 = p0 + acc1;

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
            acc6  <= sum6;
            acc5  <= sum5;
            acc4  <= sum4;
            acc3  <= sum3;
            acc2  <= sum2;
            acc1  <= sum1;
            y_out <= sum0;
        end
    end
endmodule