`timescale 1ns/1ps
// @latency 9
// Default WIDTH=8 metadata only; parameter overrides retire no earlier than WIDTH+1.
// Qualification only. Never configured as a generator seed.
module iterative_divider_core #(parameter WIDTH=8)(
    input clk, input rst,
    input [WIDTH-1:0] dividend, input [WIDTH-1:0] divisor,
    input in_valid, output in_ready,
    output reg [WIDTH-1:0] quotient, output reg [WIDTH-1:0] remainder,
    output reg out_valid, input out_ready);
    localparam STEP_BITS = (WIDTH <= 1) ? 1 : $clog2(WIDTH+1);
    reg busy;
    reg [STEP_BITS-1:0] steps_left;
    reg [WIDTH-1:0] quotient_work;
    reg [WIDTH:0] remainder_work;
    reg [WIDTH-1:0] divisor_saved, dividend_saved;
    wire [WIDTH:0] trial_remainder = (remainder_work << 1) | quotient_work[WIDTH-1];
    wire subtract_divisor = (trial_remainder >= {1'b0, divisor_saved});
    wire [WIDTH:0] next_remainder = subtract_divisor ? trial_remainder - {1'b0, divisor_saved} : trial_remainder;
    wire [WIDTH-1:0] next_quotient = (quotient_work << 1) | subtract_divisor;
    assign in_ready = !busy && (!out_valid || out_ready);
    always @(posedge clk) begin
        if(rst) begin
            busy <= 0;
            out_valid <= 0;
            steps_left <= 0;
        end else begin
            if(out_valid && out_ready) out_valid <= 0;
            if(in_valid && in_ready) begin
                dividend_saved <= dividend;
                divisor_saved <= divisor;
                quotient_work <= dividend;
                remainder_work <= 0;
                steps_left <= WIDTH;
                busy <= 1;
            end else if(busy) begin
                quotient_work <= next_quotient;
                remainder_work <= next_remainder;
                steps_left <= steps_left - 1'b1;
                if(steps_left == 1) begin
                    quotient <= (divisor_saved == 0) ? {WIDTH{1'b1}} : next_quotient;
                    remainder <= (divisor_saved == 0) ? dividend_saved : next_remainder[WIDTH-1:0];
                    busy <= 0;
                    out_valid <= 1;
                end
            end
        end
    end
endmodule
