`timescale 1ns/1ps
module mux4 (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    always @(posedge clk) begin
        if (rst)
            y <= 8'd0;
        else
            y <= sel[1] ? (sel[0] ? d : c) : (sel[0] ? b : a);
    end
endmodule