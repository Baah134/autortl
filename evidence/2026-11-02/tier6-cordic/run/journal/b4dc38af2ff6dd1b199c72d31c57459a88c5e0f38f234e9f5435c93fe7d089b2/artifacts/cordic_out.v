`timescale 1ns/1ps
// @latency 0
module cordic_out (
    input  wire [17:0] x_in,
    input  wire [17:0] y_in,
    output wire [15:0] cos_out,
    output wire [15:0] sin_out
);

    wire signed [18:0] x_extended = {x_in[17], x_in};
    wire signed [18:0] y_extended = {y_in[17], y_in};
    wire signed [18:0] x_rounded = x_extended + 19'sd2;
    wire signed [18:0] y_rounded = y_extended + 19'sd2;

    assign cos_out = x_rounded >>> 2;
    assign sin_out = y_rounded >>> 2;

endmodule