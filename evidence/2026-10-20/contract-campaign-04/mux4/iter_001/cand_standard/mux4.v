`timescale 1ns/1ps
// @latency 0
module mux4 (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [7:0] c,
    input  wire [7:0] d,
    input  wire [1:0] sel,
    output wire [7:0] y
);
    reg [7:0] y_reg;

    assign y = y_reg;

    always @(posedge clk) begin
        if (rst)
            y_reg <= 8'd0;
        else
            y_reg <= sel[1] ? (sel[0] ? d : c) : (sel[0] ? b : a);
    end
endmodule