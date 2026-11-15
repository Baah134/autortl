module TopModule (
    input  wire clk,
    input  wire a,
    input  wire b,
    output wire q,
    output reg  state
);

    assign q = a ^ b ^ state;

    always @(posedge clk)
        state <= (a & b) | (a & state) | (b & state);

endmodule
