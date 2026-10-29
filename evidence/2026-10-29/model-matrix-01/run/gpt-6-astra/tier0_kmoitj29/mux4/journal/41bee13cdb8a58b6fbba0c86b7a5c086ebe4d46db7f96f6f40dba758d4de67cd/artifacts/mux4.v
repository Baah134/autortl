`timescale 1ns/1ps
module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    reg [7:0] selected_data;

    always @(*) begin
        selected_data = d;
        case (sel)
            2'd0: selected_data = a;
            2'd1: selected_data = b;
            2'd2: selected_data = c;
            default: selected_data = d;
        endcase
    end

    always @(posedge clk) begin
        if (rst)
            y <= 8'd0;
        else
            y <= selected_data;
    end
endmodule