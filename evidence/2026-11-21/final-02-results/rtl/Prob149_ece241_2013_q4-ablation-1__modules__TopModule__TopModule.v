`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire       clk,
    input  wire       reset,
    input  wire [2:0] s,
    output wire       fr2,
    output wire       fr1,
    output wire       fr0,
    output wire       dfr
);
    reg [2:0] valves;
    reg       supplemental;
    wire [2:0] next_valves;
    wire       intermediate_direction;

    assign {fr2, fr1, fr0} = valves;
    assign dfr = supplemental;

    assign next_valves[0] = ~s[2];
    assign next_valves[1] = next_valves[0] & ~s[1];
    assign next_valves[2] = next_valves[1] & ~s[0];

    // For each intermediate level, test for a cleared valve bit
    // or retain the direction if no valve bit was newly asserted.
    assign intermediate_direction = next_valves[1]
        ? (valves[2] | (valves[1] & supplemental))
        : (valves[1] | (valves[0] & supplemental));

    always @(posedge clk) begin
        if (reset) begin
            valves       <= 3'b111;
            supplemental <= 1'b1;
        end else begin
            valves       <= next_valves;
            supplemental <= next_valves[2] |
                            (next_valves[0] & intermediate_direction);
        end
    end
endmodule