`timescale 1ns/1ps
// @latency 0
module TopModule_top (
    input wire [7:0] a,
    input wire [7:0] b,
    output wire [7:0] s,
    output wire overflow
);
    wire [7:0] lower_sum;
    wire carry_into_bit7;

    assign lower_sum = {1'b0, a[6:0]} + {1'b0, b[6:0]};
    assign carry_into_bit7 = lower_sum[7];

    assign s[6:0] = lower_sum[6:0];
    assign s[7] = a[7] ^ b[7] ^ carry_into_bit7;
    assign overflow = (~(a[7] ^ b[7])) &
                      (carry_into_bit7 ^ a[7]);
endmodule