`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire x,
    output wire z
);

    (* fsm_encoding = "none" *) reg [2:0] state;
    reg [2:0] next_state;

    always @(*) begin
        next_state = 3'b000;
        if (!reset) begin
            case (state)
                3'b000: next_state = x ? 3'b001 : 3'b000;
                3'b001: next_state = x ? 3'b100 : 3'b001;
                3'b010: next_state = x ? 3'b001 : 3'b010;
                3'b011: next_state = x ? 3'b010 : 3'b001;
                3'b100: next_state = x ? 3'b100 : 3'b011;
                default: next_state = 3'b000;
            endcase
        end
    end

    always @(posedge clk) begin
        state <= next_state;
    end

    assign z = (state == 3'b011) | (state == 3'b100);

endmodule