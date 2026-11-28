`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire areset,
    input  wire x,
    output wire z
);

    reg seen_one;
    reg z_reg;

    assign z = z_reg;

    always @(posedge clk or posedge areset) begin
        if (areset) begin
            seen_one <= 1'b0;
            z_reg    <= 1'b0;
        end else begin
            seen_one <= seen_one | x;
            z_reg    <= x ^ seen_one;
        end
    end

endmodule