`timescale 1ns/1ps
// @latency 9
module iterative_divider_core #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst,
    input wire [WIDTH-1:0] dividend,
    input wire [WIDTH-1:0] divisor,
    input wire in_valid,
    output wire in_ready,
    output wire [WIDTH-1:0] quotient,
    output wire [WIDTH-1:0] remainder,
    output wire out_valid,
    input wire out_ready
);

    reg busy;
    reg out_valid_reg;
    reg [WIDTH:0] iterations_left;
    reg [WIDTH-1:0] quotient_work;
    reg [WIDTH:0] remainder_work;
    reg [WIDTH-1:0] divisor_work;
    reg [WIDTH-1:0] dividend_saved;
    reg [WIDTH-1:0] quotient_reg;
    reg [WIDTH-1:0] remainder_reg;

    wire [WIDTH:0] trial_remainder;
    wire [WIDTH:0] divisor_extended;
    wire subtract_bit;
    wire [WIDTH:0] remainder_step;
    wire [WIDTH-1:0] quotient_step;

    assign trial_remainder = {remainder_work[WIDTH-1:0], quotient_work[WIDTH-1]};
    assign divisor_extended = {1'b0, divisor_work};
    assign subtract_bit = (trial_remainder >= divisor_extended);
    assign remainder_step = subtract_bit ? (trial_remainder - divisor_extended) : trial_remainder;
    assign quotient_step = (quotient_work << 1) | subtract_bit;

    assign in_ready = !busy && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign quotient = quotient_reg;
    assign remainder = remainder_reg;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            out_valid_reg <= 1'b0;
            iterations_left <= {(WIDTH+1){1'b0}};
            quotient_work <= {WIDTH{1'b0}};
            remainder_work <= {(WIDTH+1){1'b0}};
            divisor_work <= {WIDTH{1'b0}};
            dividend_saved <= {WIDTH{1'b0}};
            quotient_reg <= {WIDTH{1'b0}};
            remainder_reg <= {WIDTH{1'b0}};
        end else if (busy) begin
            quotient_work <= quotient_step;
            remainder_work <= remainder_step;
            iterations_left <= iterations_left - 1'b1;

            if (iterations_left != {{WIDTH{1'b0}}, 1'b1}) begin
                busy <= 1'b0;
                out_valid_reg <= 1'b1;
                if (divisor_work == {WIDTH{1'b0}}) begin
                    quotient_reg <= {WIDTH{1'b1}};
                    remainder_reg <= dividend_saved;
                end else begin
                    quotient_reg <= quotient_step;
                    remainder_reg <= remainder_step[WIDTH-1:0];
                end
            end
        end else if (out_valid_reg) begin
            if (out_ready)
                out_valid_reg <= 1'b0;
        end else if (in_valid) begin
            busy <= 1'b1;
            iterations_left <= WIDTH;
            quotient_work <= dividend;
            remainder_work <= {(WIDTH+1){1'b0}};
            divisor_work <= divisor;
            dividend_saved <= dividend;
        end
    end

endmodule