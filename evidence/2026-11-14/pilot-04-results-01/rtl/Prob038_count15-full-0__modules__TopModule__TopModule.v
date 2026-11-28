`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire       clk,
    input  wire       reset,
    output wire [3:0] q
);
    reg [3:0] count;

    assign q = count;

    always @(posedge clk) begin
        if (reset)
            count <= 4'b0000;
        else
            count <= count + 4'b0001;
    end
endmodule