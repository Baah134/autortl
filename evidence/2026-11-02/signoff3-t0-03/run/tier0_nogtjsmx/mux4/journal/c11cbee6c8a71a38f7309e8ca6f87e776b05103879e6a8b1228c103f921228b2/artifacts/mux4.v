`timescale 1ns/1ps
module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    wire sel0;
    wire sel1;
    wire sel2;
    wire sel3;
    wire [7:0] selected_data;

    assign sel0 = (sel == 2'd0);
    assign sel1 = (sel == 2'd1);
    assign sel2 = (sel == 2'd2);
    assign sel3 = (sel == 2'd3);

    assign selected_data = ({8{sel0}} & a) |
                           ({8{sel1}} & b) |
                           ({8{sel2}} & c) |
                           ({8{sel3}} & d);

    always @(posedge clk) begin
        if (rst)
            y <= 8'd0;
        else
            y <= selected_data;
    end
endmodule