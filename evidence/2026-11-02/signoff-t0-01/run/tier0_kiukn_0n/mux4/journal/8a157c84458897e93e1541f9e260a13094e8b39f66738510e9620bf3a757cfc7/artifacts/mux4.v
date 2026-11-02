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
    wire sel_a;
    wire sel_b;
    wire sel_c;
    wire sel_d;
    wire [7:0] selected;
    reg  [7:0] y_reg;

    assign sel_a = (sel == 2'd0);
    assign sel_b = (sel == 2'd1);
    assign sel_c = (sel == 2'd2);
    assign sel_d = (sel == 2'd3);

    assign selected = ({8{sel_a}} & a) |
                      ({8{sel_b}} & b) |
                      ({8{sel_c}} & c) |
                      ({8{sel_d}} & d);

    always @(posedge clk) begin
        if (rst)
            y_reg <= 8'd0;
        else
            y_reg <= selected;
    end

    assign y = y_reg;
endmodule