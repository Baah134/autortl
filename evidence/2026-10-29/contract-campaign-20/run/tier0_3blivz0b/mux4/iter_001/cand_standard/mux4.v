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
        else
            y <= {d, c, b, a}[sel * 8 +: 8];
    end
endmodule