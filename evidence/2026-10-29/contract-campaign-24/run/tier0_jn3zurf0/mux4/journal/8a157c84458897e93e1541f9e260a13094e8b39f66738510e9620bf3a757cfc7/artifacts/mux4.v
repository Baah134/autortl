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
    wire [7:0] mux_f7_0;
    wire [7:0] mux_f7_1;
    wire [7:0] mux_f8;
    reg  [7:0] y_reg;

    assign mux_f7_0 = sel[0] ? b : a;
    assign mux_f7_1 = sel[0] ? d : c;
    assign mux_f8   = sel[1] ? mux_f7_1 : mux_f7_0;
    assign y = y_reg;

    always @(posedge clk) begin
        if (rst)
            y_reg <= 8'd0;
        else
            y_reg <= mux_f8;
    end
endmodule