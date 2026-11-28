`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire [2:0] y,
    input  wire       w,
    output wire       Y1
);
    assign Y1 = (y == 3'd1) |
                (y == 3'd5) |
                ((y == 3'd2) & w) |
                ((y == 3'd3) & ~w) |
                ((y == 3'd4) & w);
endmodule