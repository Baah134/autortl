`timescale 1ns/1ps
// @latency 1
module TopModule (
    input wire clk,
    input wire reset,
    input wire in,
    output wire out
);
    reg state;

    assign out = state;

    always @(posedge clk) begin
        if (reset)
            state <= 1'b1;
        else
            state <= state ^ ~in;
    end
endmodule