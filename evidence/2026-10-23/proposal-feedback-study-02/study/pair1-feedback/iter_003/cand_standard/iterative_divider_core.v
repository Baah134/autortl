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
    reg [WIDTH-1:0] dividend_reg;
    reg [WIDTH-1:0] divisor_reg;
    reg [WIDTH-1:0] quotient_work;
    reg [WIDTH:0] remainder_work;
    reg [WIDTH-1:0] step_token;

    reg [WIDTH-1:0] quotient_reg;
    reg [WIDTH-1:0] remainder_reg;

    wire [WIDTH:0] trial_remainder;
    wire [WIDTH+1:0] trial_sub_ext;
    wire subtract_no_borrow;
    wire [WIDTH:0] next_remainder;
    wire [WIDTH-1:0] next_quotient;

    assign trial_remainder = {
        remainder_work[WIDTH-1:0],
        quotient_work[WIDTH-1]
    };

    assign trial_sub_ext =
        {1'b0, trial_remainder}
        + {1'b0, ~{1'b0, divisor_reg}}
        + {{(WIDTH+1){1'b0}}, 1'b1};

    assign subtract_no_borrow = trial_sub_ext[WIDTH+1];

    assign next_remainder = subtract_no_borrow
        ? trial_sub_ext[WIDTH:0]
        : trial_remainder;

    assign next_quotient = (quotient_work << 1) | subtract_no_borrow;

    assign in_ready = !busy && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign quotient = quotient_reg;
    assign remainder = remainder_reg;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            out_valid_reg <= 1'b0;
            dividend_reg <= {WIDTH{1'b0}};
            divisor_reg <= {WIDTH{1'b0}};
            quotient_work <= {WIDTH{1'b0}};
            remainder_work <= {(WIDTH+1){1'b0}};
            step_token <= {WIDTH{1'b0}};
            quotient_reg <= {WIDTH{1'b0}};
            remainder_reg <= {WIDTH{1'b0}};
        end else if (busy) begin
            quotient_work <= next_quotient;
            remainder_work <= next_remainder;
            step_token <= step_token << 1;

            if (step_token[WIDTH-1]) begin
                busy <= 1'b0;
                out_valid_reg <= 1'b1;
                quotient_reg <= next_quotient;
                remainder_reg <= next_remainder[WIDTH-1:0];
            end
        end else if (out_valid_reg) begin
            if (out_ready)
                out_valid_reg <= 1'b0;
        end else if (in_valid && in_ready) begin
            dividend_reg <= dividend;
            divisor_reg <= divisor;
            quotient_work <= dividend;
            remainder_work <= {(WIDTH+1){1'b0}};
            step_token <= {{(WIDTH-1){1'b0}}, 1'b1};
            busy <= 1'b1;
        end
    end

endmodule