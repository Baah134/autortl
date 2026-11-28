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

    reg signed [31:0] p0, p1, p2, p3, p4, p5, p6, p7;
    reg signed [31:0] z0, z1, z2, z3, z4, z5, z6;

    wire signed [31:0] xprod0 = x_in * C0;
    wire signed [31:0] xprod1 = x_in * C1;
    wire signed [31:0] xprod2 = x_in * C2;
    wire signed [31:0] xprod3 = x_in * C3;
    wire signed [31:0] xprod4 = x_in * C4;
    wire signed [31:0] xprod5 = x_in * C5;
    wire signed [31:0] xprod6 = x_in * C6;
    wire signed [31:0] xprod7 = x_in * C7;

    always @(posedge clk) begin
        if (rst) begin
            p0    <= 32'sd0;
            p1    <= 32'sd0;
            p2    <= 32'sd0;
            p3    <= 32'sd0;
            p4    <= 32'sd0;
            p5    <= 32'sd0;
            p6    <= 32'sd0;
            p7    <= 32'sd0;
            z0    <= 32'sd0;
            z1    <= 32'sd0;
            z2    <= 32'sd0;
            z3    <= 32'sd0;
            z4    <= 32'sd0;
            z5    <= 32'sd0;
            z6    <= 32'sd0;
            y_out <= 32'sd0;
        end else begin
            p0    <= xprod0;
            p1    <= xprod1;
            p2    <= xprod2;
            p3    <= xprod3;
            p4    <= xprod4;
            p5    <= xprod5;
            p6    <= xprod6;
            p7    <= xprod7;
            z0    <= p1 + z1;
            z1    <= p2 + z2;
            z2    <= p3 + z3;
            z3    <= p4 + z4;
            z4    <= p5 + z5;
            z5    <= p6 + z6;
            z6    <= p7;
            y_out <= p0 + z0;
        end
    end
endmodule