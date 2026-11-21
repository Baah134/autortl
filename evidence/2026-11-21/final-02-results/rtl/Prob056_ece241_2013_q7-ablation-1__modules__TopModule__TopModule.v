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
        if (q_state)
            q_state <= ~k;
        else
            q_state <= j;
    end
endmodule