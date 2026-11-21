`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire [2:0]  a,
    output wire [15:0] q
);

    // Each mask stores one output bit, with address zero at bit zero.
    function lookup_bit;
        input [7:0] mask;
        input [2:0] address;
        begin
            lookup_bit = mask[address];
        end
    endfunction

    assign q[0]  = lookup_bit(8'h80, a);
    assign q[1]  = lookup_bit(8'h79, a);
    assign q[2]  = lookup_bit(8'h7C, a);
    assign q[3]  = lookup_bit(8'hA8, a);
    assign q[4]  = lookup_bit(8'h85, a);
    assign q[5]  = lookup_bit(8'h53, a);
    assign q[6]  = lookup_bit(8'h36, a);
    assign q[7]  = lookup_bit(8'h26, a);
    assign q[8]  = lookup_bit(8'hC4, a);
    assign q[9]  = lookup_bit(8'h8F, a);
    assign q[10] = lookup_bit(8'hE6, a);
    assign q[11] = lookup_bit(8'h8A, a);
    assign q[12] = lookup_bit(8'h09, a);
    assign q[13] = lookup_bit(8'hB6, a);
    assign q[14] = lookup_bit(8'h68, a);
    assign q[15] = lookup_bit(8'h42, a);

endmodule