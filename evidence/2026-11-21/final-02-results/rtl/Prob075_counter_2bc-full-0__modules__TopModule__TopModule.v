`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire       clk,
    input  wire       areset,
    input  wire       train_valid,
    input  wire       train_taken,
    output wire [1:0] state
);

    reg [1:0] counter;
    wire [1:0] next_state;

    assign state = counter;

    assign next_state[1] = (counter[1] & counter[0]) |
                           (train_taken & (counter[1] | counter[0]));
    assign next_state[0] = train_taken ? (counter[1] | ~counter[0])
                                      : (counter[1] & ~counter[0]);

    always @(posedge clk or posedge areset) begin
        if (areset)
            counter <= 2'b01;
        else if (train_valid)
            counter <= next_state;
    end

endmodule