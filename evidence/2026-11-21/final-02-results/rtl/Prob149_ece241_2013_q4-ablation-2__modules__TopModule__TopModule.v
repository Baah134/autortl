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

    assign {fr2, fr1, fr0} = nominal;
    assign dfr = supplemental;

    always @(posedge clk) begin
        if (reset) begin
            nominal      <= 3'b111;
            supplemental <= 1'b1;
        end else begin
            case (s)
                3'b000: begin
                    nominal      <= 3'b111;
                    supplemental <= 1'b1;
                end
                3'b001: begin
                    nominal <= 3'b011;
                    if (nominal != 3'b011)
                        supplemental <= fr2;
                end
                3'b011: begin
                    nominal <= 3'b001;
                    if (nominal != 3'b001)
                        supplemental <= fr1;
                end
                3'b111: begin
                    nominal      <= 3'b000;
                    supplemental <= 1'b0;
                end
                default: begin
                    // Hold the stored level and supplemental valve state.
                end
            endcase
        end
    end

endmodule