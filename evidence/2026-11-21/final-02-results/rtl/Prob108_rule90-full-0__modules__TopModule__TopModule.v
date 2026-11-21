`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [511:0] data,
    output wire [511:0] q
);

    reg [511:0] state;
    wire [511:0] next_state;

    assign q = state;

    assign next_state[0] = load ? data[0] : q[1];
    assign next_state[511] = load ? data[511] : q[510];

    genvar i;
    generate
        for (i = 1; i < 511; i = i + 1) begin : gen_cell
            assign next_state[i] = load ? data[i] : (q[i-1] ^ q[i+1]);
        end
    endgenerate

    always @(posedge clk) begin
        state <= next_state;
    end

endmodule