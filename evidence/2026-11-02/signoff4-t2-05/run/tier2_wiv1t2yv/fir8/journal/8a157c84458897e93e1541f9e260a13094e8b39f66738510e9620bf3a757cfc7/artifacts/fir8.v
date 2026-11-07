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

    wire signed [31:0] p0 = {{16{d[0][15]}}, d[0]} * {{16{C0[15]}}, C0};
    wire signed [31:0] p1 = {{16{d[1][15]}}, d[1]} * {{16{C1[15]}}, C1};
    wire signed [31:0] p2 = {{16{d[2][15]}}, d[2]} * {{16{C2[15]}}, C2};
    wire signed [31:0] p3 = {{16{d[3][15]}}, d[3]} * {{16{C3[15]}}, C3};
    wire signed [31:0] p4 = {{16{d[4][15]}}, d[4]} * {{16{C4[15]}}, C4};
    wire signed [31:0] p5 = {{16{d[5][15]}}, d[5]} * {{16{C5[15]}}, C5};
    wire signed [31:0] p6 = {{16{d[6][15]}}, d[6]} * {{16{C6[15]}}, C6};
    wire signed [31:0] p7 = {{16{d[7][15]}}, d[7]} * {{16{C7[15]}}, C7};

    wire signed [31:0] s01 = p0 + p1;
    wire signed [31:0] s23 = p2 + p3;
    wire signed [31:0] s45 = p4 + p5;
    wire signed [31:0] s67 = p6 + p7;
    wire signed [31:0] s0123 = s01 + s23;
    wire signed [31:0] s4567 = s45 + s67;
    wire signed [31:0] sum_all = s0123 + s4567;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                d[i] <= 16'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1)
                d[i] <= d[i-1];
            y_out <= sum_all;
        end
    end
endmodule