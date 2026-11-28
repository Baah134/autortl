`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire        clk,
    input  wire        reset,
    input  wire [31:0] in,
    output wire [31:0] out
);

    reg [31:0] previous_input;
    reg [31:0] sticky;

    assign out = sticky;

    always @(posedge clk) begin
        if (reset) begin
            previous_input <= 32'b0;
            sticky         <= 32'b0;
        end else begin
            previous_input <= in;
            sticky         <= sticky | (previous_input & ~in);
        end
    end

endmodule