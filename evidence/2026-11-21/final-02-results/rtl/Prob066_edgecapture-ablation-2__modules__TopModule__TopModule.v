`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire        clk,
    input  wire        reset,
    input  wire [31:0] in,
    output wire [31:0] out
);

    reg [31:0] history;
    reg [31:0] captured;

    assign out = captured;

    always @(posedge clk) begin
        history <= in;

        if (reset)
            captured <= 32'b0;
        else
            captured <= captured | (history & ~in);
    end

endmodule