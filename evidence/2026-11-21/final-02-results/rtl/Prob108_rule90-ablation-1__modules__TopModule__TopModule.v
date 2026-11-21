`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [511:0] data,
    output wire [511:0] q
);

    reg  [511:0] state;
    wire [511:0] evolved;

    assign q = state;
    assign evolved = {state[510:0], 1'b0} ^ {1'b0, state[511:1]};

    always @(posedge clk) begin
        state <= load ? data : evolved;
    end

endmodule