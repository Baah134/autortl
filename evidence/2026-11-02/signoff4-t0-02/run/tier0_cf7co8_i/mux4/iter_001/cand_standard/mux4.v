`timescale 1ns/1ps
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
    wire [7:0] mux_lo;
    wire [7:0] mux_hi;
    wire [7:0] mux_out;
    reg  [7:0] y_reg;

    assign mux_lo = sel[0] ? b : a;
    assign mux_hi = sel[0] ? d : c;
    assign mux_out = sel[1] ? mux_hi : mux_lo;
    assign y = y_reg;

    always @(posedge clk) begin
        if (rst)
            y_reg <= 8'd0;
        else
            y_reg <= mux_out;
    end
endmodule