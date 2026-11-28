module iterative_divider_core (clk, rst, dividend, divisor, in_valid, in_ready, quotient, remainder, out_valid, out_ready);
parameter WIDTH = 8;
input wire clk;
input wire rst;
input wire [WIDTH - 1:0] dividend;
input wire [WIDTH - 1:0] divisor;
input wire in_valid;
output wire in_ready;
output wire [WIDTH - 1:0] quotient;
output wire [WIDTH - 1:0] remainder;
output wire out_valid;
input wire out_ready;
endmodule
