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
    wire [31:0] packed_data;
    wire [7:0] selected_data;
    reg  [7:0] y_reg;

    assign packed_data = {d, c, b, a};
    assign selected_data = packed_data[sel * 8 +: 8];
    assign y = y_reg;

    always @(posedge clk) begin
        if (rst)
            y_reg <= 8'd0;
        else
            y_reg <= selected_data;
    end
endmodule