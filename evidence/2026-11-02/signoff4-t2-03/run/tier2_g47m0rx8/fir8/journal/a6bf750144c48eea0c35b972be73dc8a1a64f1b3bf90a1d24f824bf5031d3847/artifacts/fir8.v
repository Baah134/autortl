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

    reg signed [15:0] d0;
    reg signed [31:0] z0, z1, z2, z3, z4, z5, z6;

    wire signed [31:0] p0 = d0 * C0;
    wire signed [31:0] p1 = d0 * C1;
    wire signed [31:0] p2 = d0 * C2;
    wire signed [31:0] p3 = d0 * C3;
    wire signed [31:0] p4 = d0 * C4;
    wire signed [31:0] p5 = d0 * C5;
    wire signed [31:0] p6 = d0 * C6;
    wire signed [31:0] p7 = d0 * C7;

    always @(posedge clk) begin
        if (rst) begin
            d0    <= 16'sd0;
            z0    <= 32'sd0;
            z1    <= 32'sd0;
            z2    <= 32'sd0;
            z3    <= 32'sd0;
            z4    <= 32'sd0;
            z5    <= 32'sd0;
            z6    <= 32'sd0;
            y_out <= 32'sd0;
        end else begin
            d0    <= x_in;
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