`timescale 1ns/1ps
module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    wire [7:0] mux_ab = sel[0] ? b : a;
    wire [7:0] mux_cd = sel[0] ? d : c;
    wire [7:0] mux_out = sel[1] ? mux_cd : mux_ab;

    always @(posedge clk) begin
        if (rst) y <= 8'd0;
        else y <= mux_out;
    end
endmodule