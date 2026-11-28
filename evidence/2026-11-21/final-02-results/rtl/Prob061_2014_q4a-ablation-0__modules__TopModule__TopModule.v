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

    wire load_enable;
    wire next_data;
    reg  q_reg;

    assign load_enable = L | E;
    assign next_data = L ? R : w;
    assign Q = q_reg;

    always @(posedge clk) begin
        if (load_enable)
            q_reg <= next_data;
    end

endmodule