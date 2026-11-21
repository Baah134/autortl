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

    reg [2:0] nominal;
    reg       supplemental;

    wire [2:0] next_nominal;

    assign {fr2, fr1, fr0} = nominal;
    assign dfr = supplemental;

    assign next_nominal[2] = ~(|s);
    assign next_nominal[1] = ~(|s[2:1]);
    assign next_nominal[0] = ~s[2];

    always @(posedge clk) begin
        if (reset) begin
            nominal      <= 3'b111;
            supplemental <= 1'b1;
        end else begin
            nominal <= next_nominal;

            // The nominal code decreases as the water level rises.
            if (next_nominal == 3'b111)
                supplemental <= 1'b1;
            else if (next_nominal == 3'b000)
                supplemental <= 1'b0;
            else if (next_nominal != nominal)
                supplemental <= (next_nominal < nominal);
        end
    end

endmodule