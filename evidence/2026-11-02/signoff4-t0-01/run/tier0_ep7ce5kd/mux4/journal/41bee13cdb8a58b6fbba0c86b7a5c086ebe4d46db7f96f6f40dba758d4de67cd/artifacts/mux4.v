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
    wire [7:0] selected_data;
    reg  [7:0] y_reg;

    assign selected_data =
        ({8{sel == 2'd0}} & a) |
        ({8{sel == 2'd1}} & b) |
        ({8{sel == 2'd2}} & c) |
        ({8{sel == 2'd3}} & d);

    always @(posedge clk) begin
        if (rst)
            y_reg <= 8'd0;
        else
            y_reg <= selected_data;
    end

    assign y = y_reg;
endmodule