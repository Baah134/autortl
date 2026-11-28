`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire x,
    output wire z
);

    localparam [2:0] STATE_000 = 3'b000;
    localparam [2:0] STATE_001 = 3'b001;
    localparam [2:0] STATE_010 = 3'b010;
    localparam [2:0] STATE_011 = 3'b101;
    localparam [2:0] STATE_100 = 3'b100;

    (* fsm_encoding = "none" *) reg [2:0] state;
    wire [2:0] next_state;

    assign next_state[2] = !reset &&
        ((state == STATE_100) || ((state == STATE_001) && x));

    assign next_state[1] = !reset &&
        (((state == STATE_010) && !x) || ((state == STATE_011) && x));

    assign next_state[0] = !reset &&
        (((state == STATE_000 || state == STATE_010) && x) ||
         ((state == STATE_001 || state == STATE_011 || state == STATE_100) && !x));

    always @(posedge clk) begin
        state <= next_state;
    end

    assign z = state[2];

endmodule