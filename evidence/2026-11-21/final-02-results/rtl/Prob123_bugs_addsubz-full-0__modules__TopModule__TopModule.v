`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire       do_sub,
    input  wire [7:0] a,
    input  wire [7:0] b,
    output wire [7:0] out,
    output wire       result_is_zero
);

    wire [7:0] b_effective;
    wire [8:0] carry;

    assign b_effective = b ^ {8{do_sub}};
    assign carry[0] = do_sub;

    genvar bit_index;
    generate
        for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin : add_bit
            wire propagate;

            assign propagate = a[bit_index] ^ b_effective[bit_index];
            assign carry[bit_index + 1] = propagate ? carry[bit_index] : a[bit_index];
            assign out[bit_index] = propagate ^ carry[bit_index];
        end
    endgenerate

    assign result_is_zero = ~|out;

endmodule