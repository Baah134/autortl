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

    reg [2:0] flow;
    reg       supplemental;
    wire      legal_sample;

    assign {fr2, fr1, fr0} = flow;
    assign dfr = supplemental;

    assign legal_sample = (!s[2] || s[1]) && (!s[1] || s[0]);

    always @(posedge clk) begin
        if (reset) begin
            flow         <= 3'b111;
            supplemental <= 1'b1;
        end else if (legal_sample) begin
            flow <= ~{s[0], s[1], s[2]};

            case (s)
                3'b000: supplemental <= 1'b1;
                3'b001: supplemental <= fr2 | (fr1 & supplemental);
                3'b011: supplemental <= fr1 | (fr0 & supplemental);
                3'b111: supplemental <= 1'b0;
                default: ;
            endcase
        end
    end

endmodule