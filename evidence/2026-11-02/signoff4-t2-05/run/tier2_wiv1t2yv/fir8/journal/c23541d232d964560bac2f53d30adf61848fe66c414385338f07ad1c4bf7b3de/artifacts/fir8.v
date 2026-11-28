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
            acc7  <= $signed({{16{x_d[15]}}, x_d}) * $signed({{16{C7[15]}}, C7});
            acc6  <= ($signed({{16{x_d[15]}}, x_d}) * $signed({{16{C6[15]}}, C6})) + acc7;
            acc5  <= ($signed({{16{x_d[15]}}, x_d}) * $signed({{16{C5[15]}}, C5})) + acc6;
            acc4  <= ($signed({{16{x_d[15]}}, x_d}) * $signed({{16{C4[15]}}, C4})) + acc5;
            acc3  <= ($signed({{16{x_d[15]}}, x_d}) * $signed({{16{C3[15]}}, C3})) + acc4;
            acc2  <= ($signed({{16{x_d[15]}}, x_d}) * $signed({{16{C2[15]}}, C2})) + acc3;
            acc1  <= ($signed({{16{x_d[15]}}, x_d}) * $signed({{16{C1[15]}}, C1})) + acc2;
            y_out <= ($signed({{16{x_d[15]}}, x_d}) * $signed({{16{C0[15]}}, C0})) + acc1;
        end
    end
endmodule