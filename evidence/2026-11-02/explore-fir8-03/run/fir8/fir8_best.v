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
    reg signed [31:0] p0, p1, p2, p3, p4, p5, p6, p7;

    wire [31:0] s1a = p0 ^ p7 ^ p1;
    wire [31:0] c1a = ((p0 & p7) | (p0 & p1) | (p7 & p1)) << 1;
    wire [31:0] s1b = p6 ^ p2 ^ p5;
    wire [31:0] c1b = ((p6 & p2) | (p6 & p5) | (p2 & p5)) << 1;

    wire [31:0] s2a = s1a ^ c1a ^ s1b;
    wire [31:0] c2a = ((s1a & c1a) | (s1a & s1b) | (c1a & s1b)) << 1;
    wire [31:0] s2b = c1b ^ p3 ^ p4;
    wire [31:0] c2b = ((c1b & p3) | (c1b & p4) | (p3 & p4)) << 1;

    wire [31:0] s3a = s2a ^ c2a ^ s2b;
    wire [31:0] c3a = ((s2a & c2a) | (s2a & s2b) | (c2a & s2b)) << 1;

    wire [31:0] s4a = s3a ^ c3a ^ c2b;
    wire [31:0] c4a = ((s3a & c3a) | (s3a & c2b) | (c3a & c2b)) << 1;

    wire [31:0] sum = s4a + c4a;

    integer i;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 10; i = i + 1)
                d[i] <= 16'sd0;
            p0 <= 32'sd0;
            p1 <= 32'sd0;
            p2 <= 32'sd0;
            p3 <= 32'sd0;
            p4 <= 32'sd0;
            p5 <= 32'sd0;
            p6 <= 32'sd0;
            p7 <= 32'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 10; i = i + 1)
                d[i] <= d[i-1];

            p0 <= d[1] * C0;
            p1 <= d[2] * C1;
            p2 <= d[3] * C2;
            p3 <= d[4] * C3;
            p4 <= d[5] * C4;
            p5 <= d[6] * C5;
            p6 <= d[7] * C6;
            p7 <= d[8] * C7;

            y_out <= sum;
        end
    end
endmodule