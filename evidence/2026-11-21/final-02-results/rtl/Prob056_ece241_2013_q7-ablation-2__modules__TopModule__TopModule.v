`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire j,
    input  wire k,
    output wire Q
);

    reg q_reg;

    assign Q = q_reg;

    always @(posedge clk) begin
        q_reg <= (j & ~q_reg) | (~k & q_reg);
    end

endmodule