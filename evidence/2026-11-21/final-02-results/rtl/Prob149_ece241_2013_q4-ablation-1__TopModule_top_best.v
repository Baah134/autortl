`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input wire clk,
    input wire reset,
    input wire [2:0] s,
    output wire fr2,
    output wire fr1,
    output wire fr0,
    output wire dfr
);
    reg [3:0] outputs_q;
    wire next_fr2;
    wire next_fr1;
    wire next_fr0;
    wire next_dfr;

    assign {fr2, fr1, fr0, dfr} = outputs_q;

    // The two zero tests share sensor inputs for dual-output LUT packing.
    // Vivado determines the physical packing.
    assign next_fr2 = ~|s;
    assign next_fr1 = ~|s[2:1];
    assign next_fr0 = ~s[2];

    // The typed transition rule and the reduced logic give the same next dfr
    // for every reachable prior output vector with reset low.
    // Prior vector     000  001  010  011  100 through 111
    //     1111          1    1    1    1          0
    //     0110          1    0    1    1          0
    //     0111          1    1    1    1          0
    //     0010          1    0    0    0          0
    //     0011          1    0    1    1          0
    //     0000          1    0    0    0          0
    // Reset overrides every pattern and selects 1111, the first row used
    // when sampling resumes.
    assign next_dfr = next_fr2 |
                      (next_fr0 & (next_fr1 ? (fr1 & dfr) : (fr1 | dfr)));

    always @(posedge clk) begin
        if (reset)
            outputs_q <= 4'b1111;
        else
            outputs_q <= {next_fr2, next_fr1, next_fr0, next_dfr};
    end
endmodule