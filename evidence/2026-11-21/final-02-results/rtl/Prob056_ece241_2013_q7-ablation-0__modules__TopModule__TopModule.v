`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire j,
    input  wire k,
    output wire Q
);

    reg q_state;

    assign Q = q_state;

    always @(posedge clk) begin
        q_state <= (j & ~q_state) | (~k & q_state);
    end

endmodule