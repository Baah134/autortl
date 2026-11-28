`timescale 1ns/1ps
// @latency 1
module TopModule (
    input wire clk,
    input wire a,
    input wire b,
    output wire q,
    output wire state
);
    reg carry;

    assign state = carry;
    assign q = a ^ b ^ carry;

    always @(posedge clk) begin
        carry <= (a & b) | (a & carry) | (b & carry);
    end
endmodule