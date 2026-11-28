`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire x,
    output wire z
);

    (* fsm_encoding = "none" *) reg [2:0] state;
    wire [2:0] next_state;
    wire state_001;
    wire state_011;
    wire state_100;

    assign state_001 = ~state[2] & ~state[1] &  state[0];
    assign state_011 = ~state[2] &  state[1] &  state[0];
    assign state_100 =  state[2] & ~state[1] & ~state[0];

    assign next_state[2] = x & (state_001 | state_100);
    assign next_state[1] = (~state[2] & state[1] & ~(state[0] ^ x))
                         | (state_100 & ~x);
    assign next_state[0] = (~state[2] & (state[0] ^ x))
                         | (state_100 & ~x);

    assign z = state_011 | state_100;

    always @(posedge clk) begin
        if (reset)
            state <= 3'b000;
        else
            state <= next_state;
    end

endmodule