`timescale 1ns/1ps
module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    wire [7:0] ab_sel;
    wire [7:0] cd_sel;
    wire [7:0] mux_sel;

    assign ab_sel  = sel[0] ? b : a;
    assign cd_sel  = sel[0] ? d : c;
    assign mux_sel = sel[1] ? cd_sel : ab_sel;

    always @(posedge clk) begin
        if (rst) y <= 8'd0;
        else y <= mux_sel;
    end
endmodule