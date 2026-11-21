`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire        clk,
    input  wire        reset,
    input  wire [31:0] in,
    output wire [31:0] out
);

    reg [31:0] previous_in;
    reg [31:0] out_reg;

    assign out = out_reg;

    always @(posedge clk) begin
        previous_in <= in;

        if (reset)
            out_reg <= 32'b0;
        else
            out_reg <= out_reg | (previous_in & ~in);
    end

endmodule