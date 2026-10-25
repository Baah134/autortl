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
        else y <= (sel == 2'd0) ? a :
                  (sel == 2'd1) ? b :
                  (sel == 2'd2) ? c : d;
    end
endmodule