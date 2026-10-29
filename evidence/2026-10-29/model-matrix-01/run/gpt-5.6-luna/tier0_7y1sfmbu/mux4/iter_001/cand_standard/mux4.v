`timescale 1ns/1ps
module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    always @(posedge clk) begin
        if (rst)
            y <= 8'd0;
        else if (sel == 2'd0)
            y <= a;
        else if (sel == 2'd1)
            y <= b;
        else if (sel == 2'd2)
            y <= c;
        else
            y <= d;
    end
endmodule