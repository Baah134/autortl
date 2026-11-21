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
    reg  [63:0] shifted;
    wire        update_enable;
    wire [63:0] next_state;

    assign q = state;
    assign update_enable = load | ena;
    assign next_state = load ? data : shifted;

    always @(*) begin
        shifted = {state[62:0], 1'b0};
        case (amount)
            2'd1: shifted = {state[55:0], 8'b0};
            2'd2: shifted = {state[63], state[63:1]};
            2'd3: shifted = {{8{state[63]}}, state[63:8]};
            default: ;
        endcase
    end

    always @(posedge clk) begin
        if (update_enable)
            state <= next_state;
    end
endmodule