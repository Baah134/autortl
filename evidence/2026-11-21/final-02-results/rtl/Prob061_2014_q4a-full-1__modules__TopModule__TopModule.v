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

    reg q_reg;
    (* keep = "true" *) wire q_next;

    assign q_next = L ? R : (E ? w : q_reg);
    assign Q = q_reg;

    always @(posedge clk) begin
        q_reg <= q_next;
    end

endmodule