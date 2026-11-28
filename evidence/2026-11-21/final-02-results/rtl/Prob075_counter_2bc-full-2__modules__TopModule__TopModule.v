`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire       clk,
    input  wire       areset,
    input  wire       train_valid,
    input  wire       train_taken,
    output wire [1:0] state
);

    reg state_hi;
    reg state_lo;
    wire next_hi;
    wire next_lo;

    assign state = {state_hi, state_lo};
    assign next_hi = (state_hi & state_lo) |
                     (train_taken & (state_hi | state_lo));
    assign next_lo = train_taken ? (state_hi | ~state_lo)
                                 : (state_hi & ~state_lo);

    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state_hi <= 1'b0;
            state_lo <= 1'b1;
        end else if (train_valid) begin
            state_hi <= next_hi;
            state_lo <= next_lo;
        end
    end

endmodule