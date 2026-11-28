`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire [2:0]  a,
    output wire [15:0] q
);
    reg [15:0] lookup;

    always @(*) begin
        lookup = 16'h0000;
        case (a)
            3'd0: lookup = 16'h1232;
            3'd1: lookup = 16'hAEE0;
            3'd2: lookup = 16'h27D4;
            3'd3: lookup = 16'h5A0E;
            3'd4: lookup = 16'h2066;
            3'd5: lookup = 16'h64CE;
            3'd6: lookup = 16'hC526;
            3'd7: lookup = 16'h2F19;
            default: lookup = 16'h0000;
        endcase
    end

    assign q = lookup;
endmodule