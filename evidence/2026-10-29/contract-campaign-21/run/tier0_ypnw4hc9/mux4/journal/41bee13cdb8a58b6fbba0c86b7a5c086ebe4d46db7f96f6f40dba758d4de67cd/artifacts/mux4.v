`timescale 1ns/1ps
module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    wire [7:0] muxf7_low;
    wire [7:0] muxf7_high;
    wire [7:0] muxf8_result;

    assign muxf7_low  = sel[0] ? b : a;
    assign muxf7_high = sel[0] ? d : c;
    assign muxf8_result = sel[1] ? muxf7_high : muxf7_low;

    always @(posedge clk) begin
        if (rst)
            y <= 8'd0;
        else
            y <= muxf8_result;
    end
endmodule