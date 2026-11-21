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

    assign next_state[0] = (!state[2] && (state[0] ^ x)) ||
                           ((state == 3'b100) && !x);
    assign next_state[1] = ((state == 3'b010) && !x) ||
                           ((state == 3'b011) && x) ||
                           ((state == 3'b100) && !x);
    assign next_state[2] = x && ((state == 3'b001) || (state == 3'b100));
    assign z = (state == 3'b011) || (state == 3'b100);

    always @(posedge clk) begin
        if (reset)
            state <= 3'b000;
        else
            state <= next_state;
    end
endmodule