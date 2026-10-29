`timescale 1ns/1ps
module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    wire sel_a = (sel == 2'd0);
    wire sel_b = (sel == 2'd1);
    wire sel_c = (sel == 2'd2);
    wire sel_d = (sel == 2'd3);

    always @(posedge clk) begin
        if (rst) y <= 8'd0;
        else y <= ({8{sel_a}} & a) |
                  ({8{sel_b}} & b) |
                  ({8{sel_c}} & c) |
                  ({8{sel_d}} & d);
    end
endmodule