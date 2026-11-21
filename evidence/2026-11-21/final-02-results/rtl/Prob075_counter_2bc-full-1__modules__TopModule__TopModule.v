`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire       clk,
    input  wire       areset,
    input  wire       train_valid,
    input  wire       train_taken,
    output wire [1:0] state
);

    reg state_msb;
    reg state_lsb;
    wire next_msb;
    wire next_lsb;

    assign state = {state_msb, state_lsb};

    assign next_msb = (state_msb & state_lsb) |
                      (train_taken & (state_msb | state_lsb));
    assign next_lsb = (state_msb & ~state_lsb) |
                      (train_taken & (state_msb | ~state_lsb));

    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state_msb <= 1'b0;
            state_lsb <= 1'b1;
        end else if (train_valid) begin
            state_msb <= next_msb;
            state_lsb <= next_lsb;
        end
    end

endmodule