`timescale 1ns/1ps
module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output wire [7:0] y
);
    wire [7:0] ab = sel[0] ? b : a;
    wire [7:0] cd = sel[0] ? d : c;
    wire [7:0] mux_out = sel[1] ? cd : ab;
    reg  [7:0] y_reg;

    assign y = y_reg;

    always @(posedge clk) begin
        if (rst)
            y_reg <= 8'd0;
        else
            y_reg <= mux_out;
    end
endmodule