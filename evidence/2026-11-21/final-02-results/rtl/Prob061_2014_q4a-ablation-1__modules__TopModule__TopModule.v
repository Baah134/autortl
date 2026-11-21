`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire w,
    input  wire R,
    input  wire E,
    input  wire L,
    output wire Q
);
    (* EXTRACT_ENABLE = "no" *) reg q_reg;

    assign Q = q_reg;

    always @(posedge clk) begin
        q_reg <= L ? R : (E ? w : q_reg);
    end
endmodule