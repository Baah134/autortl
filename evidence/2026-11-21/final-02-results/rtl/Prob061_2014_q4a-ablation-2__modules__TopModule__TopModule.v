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
    wire capture_enable;
    wire capture_data;
    reg q_reg;

    assign capture_enable = L | E;
    assign capture_data = L ? R : w;
    assign Q = q_reg;

    always @(posedge clk) begin
        if (capture_enable)
            q_reg <= capture_data;
    end
endmodule