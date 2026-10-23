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
    iterative_divider_core #( .WIDTH(8) ) u_iterative_divider_core (
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
