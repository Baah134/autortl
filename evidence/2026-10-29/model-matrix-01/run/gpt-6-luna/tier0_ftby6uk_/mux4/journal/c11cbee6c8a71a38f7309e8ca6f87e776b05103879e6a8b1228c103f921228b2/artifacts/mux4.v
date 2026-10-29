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
    wire [7:0] low_pair;
    wire [7:0] high_pair;
    wire [7:0] mux_data;
    reg  [7:0] y_reg;

    assign low_pair  = sel[0] ? b : a;
    assign high_pair = sel[0] ? d : c;
    assign mux_data  = sel[1] ? high_pair : low_pair;
    assign y = y_reg;

    always @(posedge clk) begin
        if (rst)
            y_reg <= 8'd0;
        else
            y_reg <= mux_data;
    end
endmodule