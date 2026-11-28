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

    reg signed [15:0] d [0:7];
    reg signed [31:0] p [0:7];
    integer i;

    wire signed [31:0] s01 = p[0] + p[1];
    wire signed [31:0] s23 = p[2] + p[3];
    wire signed [31:0] s45 = p[4] + p[5];
    wire signed [31:0] s67 = p[6] + p[7];
    wire signed [31:0] s0123 = s01 + s23;
    wire signed [31:0] s4567 = s45 + s67;
    wire signed [31:0] sum_all = s0123 + s4567;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1) begin
                d[i] <= 16'sd0;
                p[i] <= 32'sd0;
            end
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            p[0] <= x_in * C0;
            for (i = 1; i < 8; i = i + 1) begin
                d[i] <= d[i-1];
            end
            p[1] <= d[0] * C1;
            p[2] <= d[1] * C2;
            p[3] <= d[2] * C3;
            p[4] <= d[3] * C4;
            p[5] <= d[4] * C5;
            p[6] <= d[5] * C6;
            p[7] <= d[6] * C7;
            y_out <= sum_all;
        end
    end
endmodule