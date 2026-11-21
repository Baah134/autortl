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

    reg [63:0] state;
    reg [63:0] shifted;

    wire        clock_enable;
    wire [63:0] left_one;
    wire [63:0] left_eight;
    wire [63:0] right_one;
    wire [63:0] right_eight;
    wire [63:0] next_state;

    assign q = state;
    assign clock_enable = load | ena;

    assign left_one    = {state[62:0], 1'b0};
    assign left_eight  = {state[55:0], 8'b0};
    assign right_one   = {state[63], state[63:1]};
    assign right_eight = {{8{state[63]}}, state[63:8]};

    always @(*) begin
        shifted = 64'b0;
        case (amount)
            2'b00: shifted = left_one;
            2'b01: shifted = left_eight;
            2'b10: shifted = right_one;
            2'b11: shifted = right_eight;
        endcase
    end

    assign next_state = load ? data : shifted;

    always @(posedge clk) begin
        if (clock_enable)
            state <= next_state;
    end

endmodule