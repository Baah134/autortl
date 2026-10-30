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

    localparam COUNT_WIDTH = (WIDTH <= 1) ? 1 : $clog2(WIDTH);

    reg busy;
    reg out_valid_reg;
    reg [COUNT_WIDTH-1:0] iteration_count;

    reg [WIDTH-1:0] divisor_hold;
    reg [WIDTH-1:0] dividend_hold;
    reg [WIDTH-1:0] quotient_work;
    reg [WIDTH:0] remainder_work;

    reg [WIDTH:0] remainder_trial;
    reg [WIDTH:0] divisor_extended;
    reg [WIDTH:0] remainder_difference;
    reg [WIDTH:0] remainder_step;
    reg [WIDTH-1:0] quotient_step;

    reg [WIDTH-1:0] quotient_reg;
    reg [WIDTH-1:0] remainder_reg;

    assign in_ready = !busy && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign quotient = quotient_reg;
    assign remainder = remainder_reg;

    always @(*) begin
        remainder_trial = {remainder_work[WIDTH-1:0], quotient_work[WIDTH-1]};
        divisor_extended = {1'b0, divisor_hold};
        remainder_difference = remainder_trial - divisor_extended;

        remainder_step = remainder_trial;
        quotient_step = quotient_work << 1;

        if (remainder_trial >= divisor_extended) begin
            remainder_step = remainder_difference;
            quotient_step[0] = 1'b1;
        end else begin
            quotient_step[0] = 1'b0;
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            out_valid_reg <= 1'b0;
            iteration_count <= {COUNT_WIDTH{1'b0}};
            divisor_hold <= {WIDTH{1'b0}};
            dividend_hold <= {WIDTH{1'b0}};
            quotient_work <= {WIDTH{1'b0}};
            remainder_work <= {(WIDTH+1){1'b0}};
            quotient_reg <= {WIDTH{1'b0}};
            remainder_reg <= {WIDTH{1'b0}};
        end else begin
            if (out_valid_reg && out_ready)
                out_valid_reg <= 1'b0;

            if (in_valid && in_ready) begin
                busy <= 1'b1;
                iteration_count <= {COUNT_WIDTH{1'b0}};
                divisor_hold <= divisor;
                dividend_hold <= dividend;
                quotient_work <= dividend;
                remainder_work <= {(WIDTH+1){1'b0}};
            end else if (busy) begin
                quotient_work <= quotient_step;
                remainder_work <= remainder_step;

                if (iteration_count != WIDTH - 1) begin
                    busy <= 1'b0;
                    out_valid_reg <= 1'b1;
                    quotient_reg <= quotient_step;
                    remainder_reg <= remainder_step[WIDTH-1:0];
                end else begin
                    iteration_count <= iteration_count + 1'b1;
                end
            end
        end
    end

endmodule