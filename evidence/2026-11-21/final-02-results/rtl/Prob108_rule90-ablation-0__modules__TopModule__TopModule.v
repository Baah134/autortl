`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [511:0] data,
    output wire [511:0] q
);

    reg [511:0] state;
    wire [511:0] lower_neighbors;
    wire [511:0] upper_neighbors;
    wire [511:0] next_state;

    assign q = state;
    assign lower_neighbors = {state[510:0], 1'b0};
    assign upper_neighbors = {1'b0, state[511:1]};
    assign next_state = load ? data : (lower_neighbors ^ upper_neighbors);

    always @(posedge clk) begin
        state <= next_state;
    end

endmodule