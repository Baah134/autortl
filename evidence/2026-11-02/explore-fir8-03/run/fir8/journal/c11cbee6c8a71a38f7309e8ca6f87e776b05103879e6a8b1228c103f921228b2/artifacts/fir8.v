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

    reg signed [15:0] d [0:9];
    wire signed [31:0] p0 = d[2] * C0;
    wire signed [31:0] p1 = d[3] * C1;
    wire signed [31:0] p2 = d[4] * C2;
    wire signed [31:0] p3 = d[5] * C3;
    wire signed [31:0] p4 = d[6] * C4;
    wire signed [31:0] p5 = d[7] * C5;
    wire signed [31:0] p6 = d[8] * C6;
    wire signed [31:0] p7 = d[9] * C7;

    wire signed [31:0] s01 = p0 + p1;
    wire signed [31:0] s23 = p2 + p3;
    wire signed [31:0] s45 = p4 + p5;
    wire signed [31:0] s67 = p6 + p7;
    wire signed [31:0] s0123 = s01 + s23;
    wire signed [31:0] s4567 = s45 + s67;
    wire signed [31:0] sum = s0123 + s4567;

    integer i;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 10; i = i + 1)
                d[i] <= 16'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 10; i = i + 1)
                d[i] <= d[i-1];
            y_out <= sum;
        end
    end
endmodule