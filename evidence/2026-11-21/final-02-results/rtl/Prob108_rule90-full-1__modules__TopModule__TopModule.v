`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [511:0] data,
    output wire [511:0] q
);

    reg [511:0] state;

    assign q = state;

    always @(posedge clk) begin
        if (load)
            state <= data;
        else
            state <= {1'b0, state[511:1]} ^ {state[510:0], 1'b0};
    end

endmodule