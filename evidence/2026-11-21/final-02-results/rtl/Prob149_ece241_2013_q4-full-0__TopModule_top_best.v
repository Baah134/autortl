`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input  wire       clk,
    input  wire       reset,
    input  wire [2:0] s,
    output wire       fr2,
    output wire       fr1,
    output wire       fr0,
    output wire       dfr
);
    reg [2:0] nominal;
    reg       supplemental;

    wire [2:0] next_nominal;
    wire       next_supplemental;

    assign {fr2, fr1, fr0} = nominal;
    assign dfr = supplemental;

    assign next_nominal[2] = ~|s;
    assign next_nominal[1] = ~|s[2:1];
    assign next_nominal[0] = ~s[2];

    // A previous level of 3 always has dfr cleared.
    assign next_supplemental = ~s[2] &
        (s[1] ? (fr1 | dfr) : (~s[0] | fr2 | (fr1 & dfr)));

    always @(posedge clk) begin
        if (reset) begin
            nominal      <= 3'b111;
            supplemental <= 1'b1;
        end else begin
            nominal      <= next_nominal;
            supplemental <= next_supplemental;
        end
    end
endmodule