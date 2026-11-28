`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire       clk,
    input  wire       reset,
    output wire [4:0] q
);

    reg [4:0] state;

    assign q = state;

    always @(posedge clk) begin
        if (reset)
            state <= 5'b00001;
        else
            state <= {state[0], state[4], state[3] ^ state[0], state[2], state[1]};
    end

endmodule