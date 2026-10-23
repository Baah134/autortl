`timescale 1ns/1ps
// @latency 9
module iterative_divider (
    input wire clk,
    input wire rst,
    input wire [7:0] dividend,
    input wire [7:0] divisor,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] quotient,
    output wire [7:0] remainder,
    output wire out_valid,
    input wire out_ready
);
    reg busy;
    reg out_valid_reg;
    reg [7:0] divisor_reg;
    reg [7:0] quotient_work;
    reg [8:0] remainder_work;
    reg [3:0] iteration;

    wire [8:0] trial_remainder;
    wire [9:0] subtract_result;
    wire [8:0] next_remainder;
    wire [7:0] next_quotient;

    assign trial_remainder = {
        remainder_work[7:0],
        quotient_work[7]
    };

    assign subtract_result =
        {1'b0, trial_remainder} - {2'b00, divisor_reg};

    assign next_remainder = subtract_result[9]
        ? trial_remainder
        : subtract_result[8:0];

    assign next_quotient = {
        quotient_work[6:0],
        ~subtract_result[9]
    };

    assign in_ready = !busy && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign quotient = quotient_work;
    assign remainder = remainder_work[7:0];

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            out_valid_reg <= 1'b0;
            divisor_reg <= 8'b0;
            quotient_work <= 8'b0;
            remainder_work <= 9'b0;
            iteration <= 4'b0;
        end else if (busy) begin
            quotient_work <= next_quotient;
            remainder_work <= next_remainder;

            if (iteration == 4'd7) begin
                busy <= 1'b0;
                out_valid_reg <= 1'b1;
            end else begin
                iteration <= iteration + 1'b1;
            end
        end else if (out_valid_reg) begin
            if (out_ready)
                out_valid_reg <= 1'b0;
        end else if (in_valid && in_ready) begin
            divisor_reg <= divisor;
            quotient_work <= dividend;
            remainder_work <= 9'b0;
            iteration <= 4'b0;
            busy <= 1'b1;
        end
    end
endmodule