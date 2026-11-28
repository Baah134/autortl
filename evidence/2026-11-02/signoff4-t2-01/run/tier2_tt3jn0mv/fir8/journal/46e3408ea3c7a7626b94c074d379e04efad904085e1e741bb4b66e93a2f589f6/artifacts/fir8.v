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
    reg signed [31:0] s0, s1, s2, s3, s4, s5, s6;

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
            x_d  <= 16'sd0;
            s0   <= 32'sd0;
            s1   <= 32'sd0;
            s2   <= 32'sd0;
            s3   <= 32'sd0;
            s4   <= 32'sd0;
            s5   <= 32'sd0;
            s6   <= 32'sd0;
            y_out <= 32'sd0;
        end else begin
            x_d  <= x_in;
            s6   <= p7;
            s5   <= p6 + s6;
            s4   <= p5 + s5;
            s3   <= p4 + s4;
            s2   <= p3 + s3;
            s1   <= p2 + s2;
            s0   <= p1 + s1;
            y_out <= p0 + s0;
        end
    end
endmodule