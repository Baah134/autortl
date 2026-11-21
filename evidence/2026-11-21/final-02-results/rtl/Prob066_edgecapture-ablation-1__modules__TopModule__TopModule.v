`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire        clk,
    input  wire        reset,
    input  wire [31:0] in,
    output wire [31:0] out
);

    reg [31:0] previous_in;
    reg [31:0] sticky_out;

    assign out = sticky_out;

    always @(posedge clk) begin
        if (reset) begin
            previous_in <= 32'b0;
            sticky_out  <= 32'b0;
        end else begin
            previous_in <= in;
            sticky_out  <= sticky_out | (previous_in & ~in);
        end
    end

endmodule