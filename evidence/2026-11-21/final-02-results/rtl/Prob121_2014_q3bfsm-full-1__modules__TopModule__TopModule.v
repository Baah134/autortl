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
    wire in_000;
    wire in_001;
    wire in_010;
    wire in_011;
    wire in_100;

    assign in_000 = (state == 3'b000);
    assign in_001 = (state == 3'b001);
    assign in_010 = (state == 3'b010);
    assign in_011 = (state == 3'b011);
    assign in_100 = (state == 3'b100);

    assign next_state[2] = x & (in_001 | in_100);
    assign next_state[1] = x ? in_011 : (in_010 | in_100);
    assign next_state[0] = x ? (in_000 | in_010)
                             : (in_001 | in_011 | in_100);

    always @(posedge clk) begin
        if (reset)
            state <= 3'b000;
        else
            state <= next_state;
    end

    assign z = in_011 | in_100;

endmodule