`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire        clk,
    input  wire        load,
    input  wire        ena,
    input  wire [1:0]  amount,
    input  wire [63:0] data,
    output wire [63:0] q
);

    reg  [63:0] state;
    wire        state_enable;
    wire [63:0] left_one;
    wire [63:0] left_eight;
    wire [63:0] right_one;
    wire [63:0] right_eight;
    wire [63:0] left_branch;
    wire [63:0] right_branch;
    wire [63:0] next_state;

    assign q = state;
    assign state_enable = load | ena;

    assign left_one    = {state[62:0], 1'b0};
    assign left_eight  = {state[55:0], 8'b0};
    assign right_one   = {state[63], state[63:1]};
    assign right_eight = {{8{state[63]}}, state[63:8]};

    assign left_branch  = load ? data : (amount[0] ? left_eight : left_one);
    assign right_branch = load ? data : (amount[0] ? right_eight : right_one);
    assign next_state   = amount[1] ? right_branch : left_branch;

    always @(posedge clk) begin
        if (state_enable)
            state <= next_state;
    end

endmodule