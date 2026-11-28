`timescale 1ns/1ps
// Deliberately naive 8-tap FIR: single-cycle sum of 8 products.
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

    wire signed [31:0] p0 = $signed(d[0]) * $signed(C0);
    wire signed [31:0] p1 = $signed(d[1]) * $signed(C1);
    wire signed [31:0] p2 = $signed(d[2]) * $signed(C2);
    wire signed [31:0] p3 = $signed(d[3]) * $signed(C3);
    wire signed [31:0] p4 = $signed(d[4]) * $signed(C4);
    wire signed [31:0] p5 = $signed(d[5]) * $signed(C5);
    wire signed [31:0] p6 = $signed(d[6]) * $signed(C6);
    wire signed [31:0] p7 = $signed(d[7]) * $signed(C7);

    wire signed [31:0] s01 = p0 + p1;
    wire signed [31:0] s23 = p2 + p3;
    wire signed [31:0] s45 = p4 + p5;
    wire signed [31:0] s67 = p6 + p7;

    wire signed [31:0] s03 = s01 + s23;
    wire signed [31:0] s47 = s45 + s67;
    wire signed [31:0] sum = s03 + s47;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1) d[i] <= 16'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1) d[i] <= d[i-1];
            y_out <= sum;
        end
    end
endmodule