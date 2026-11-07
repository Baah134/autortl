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
    integer i;

    wire signed [31:0] p0 = d[0] * C0;
    wire signed [31:0] p1 = d[1] * C1;
    wire signed [31:0] p2 = d[2] * C2;
    wire signed [31:0] p3 = d[3] * C3;
    wire signed [31:0] p4 = d[4] * C4;
    wire signed [31:0] p5 = d[5] * C5;
    wire signed [31:0] p6 = d[6] * C6;
    wire signed [31:0] p7 = d[7] * C7;

    wire [31:0] s0 = p0 ^ p1 ^ p2;
    wire [31:0] c0 = ((p0 & p1) | (p0 & p2) | (p1 & p2)) << 1;
    wire [31:0] s1 = p3 ^ p4 ^ p5;
    wire [31:0] c1 = ((p3 & p4) | (p3 & p5) | (p4 & p5)) << 1;

    wire [31:0] s2 = s0 ^ c0 ^ p6;
    wire [31:0] c2 = ((s0 & c0) | (s0 & p6) | (c0 & p6)) << 1;
    wire [31:0] s3 = s1 ^ c1 ^ p7;
    wire [31:0] c3 = ((s1 & c1) | (s1 & p7) | (c1 & p7)) << 1;

    wire [31:0] s4 = s2 ^ c2 ^ s3;
    wire [31:0] c4 = ((s2 & c2) | (s2 & s3) | (c2 & s3)) << 1;

    wire [31:0] s5 = s4 ^ c4 ^ c3;
    wire [31:0] c5 = ((s4 & c4) | (s4 & c3) | (c4 & c3)) << 1;
    wire signed [31:0] total = s5 + c5;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                d[i] <= 16'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1)
                d[i] <= d[i-1];
            y_out <= total;
        end
    end
endmodule