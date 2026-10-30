`timescale 1ns/1ps
module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    always @(posedge clk) begin
        if (rst) y <= 8'd0;
        else y <= ({8{sel == 2'd0}} & a) |
                  ({8{sel == 2'd1}} & b) |
                  ({8{sel == 2'd2}} & c) |
                  ({8{sel == 2'd3}} & d);
    end
endmodule