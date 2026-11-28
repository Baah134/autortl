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
    reg result_valid;
    reg [WIDTH-1:0] divisor_reg;
    reg [WIDTH:0] remainder_work;
    reg [WIDTH-1:0] quotient_work;
    reg [WIDTH-1:0] quotient_reg;
    reg [WIDTH-1:0] remainder_reg;
    reg [WIDTH-1:0] iteration_count;

    wire [WIDTH:0] trial_remainder;
    wire [WIDTH:0] divisor_extended;
    wire [WIDTH+1:0] subtract_result;
    wire subtract_trial;
    wire [WIDTH:0] reduced_remainder;
    wire [WIDTH-1:0] quotient_next;

    assign in_ready = !busy && !result_valid;
    assign out_valid = result_valid;
    assign quotient = quotient_reg;
    assign remainder = remainder_reg;

    assign trial_remainder = {remainder_work[WIDTH-1:0], quotient_work[WIDTH-1]};
    assign divisor_extended = {1'b0, divisor_reg};
    assign subtract_result = {1'b0, trial_remainder} - {1'b0, divisor_extended};
    assign subtract_trial = !subtract_result[WIDTH+1];
    assign reduced_remainder = subtract_trial
                             ? subtract_result[WIDTH:0]
                             : trial_remainder;
    assign quotient_next = (quotient_work << 1) | subtract_trial;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            result_valid <= 1'b0;
            divisor_reg <= {WIDTH{1'b0}};
            remainder_work <= {(WIDTH+1){1'b0}};
            quotient_work <= {WIDTH{1'b0}};
            quotient_reg <= {WIDTH{1'b0}};
            remainder_reg <= {WIDTH{1'b0}};
            iteration_count <= {WIDTH{1'b0}};
        end else if (busy) begin
            if (divisor_reg != {WIDTH{1'b0}})
                remainder_work <= reduced_remainder;
            quotient_work <= quotient_next;

            if (iteration_count == WIDTH - 1) begin
                busy <= 1'b0;
                result_valid <= 1'b1;
                quotient_reg <= quotient_next;
                if (divisor_reg == {WIDTH{1'b0}})
                    remainder_reg <= remainder_work[WIDTH-1:0];
                else
                    remainder_reg <= reduced_remainder[WIDTH-1:0];
            end else begin
                iteration_count <= iteration_count + 1'b1;
            end
        end else if (result_valid) begin
            if (out_ready)
                result_valid <= 1'b0;
        end else if (in_valid && in_ready) begin
            busy <= 1'b1;
            divisor_reg <= divisor;
            if (divisor == {WIDTH{1'b0}})
                remainder_work <= {1'b0, dividend};
            else
                remainder_work <= {(WIDTH+1){1'b0}};
            quotient_work <= dividend;
            iteration_count <= {WIDTH{1'b0}};
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 9
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
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
    iterative_divider_core #(.WIDTH(8)) u_iterative_divider_core (
        .clk(clk),
        .rst(rst),
        .dividend(dividend),
        .divisor(divisor),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .quotient(quotient),
        .remainder(remainder),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule