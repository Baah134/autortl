`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire [2:0]  a,
    output wire [15:0] q
);
    function lut_bit;
        input [7:0] truth_table;
        input [2:0] address;
        begin
            lut_bit = truth_table[address];
        end
    endfunction

    assign q[15] = lut_bit(8'h42, a);
    assign q[14] = lut_bit(8'h68, a);
    assign q[13] = lut_bit(8'hB6, a);
    assign q[12] = lut_bit(8'h09, a);
    assign q[11] = lut_bit(8'h8A, a);
    assign q[10] = lut_bit(8'hE6, a);
    assign q[9]  = lut_bit(8'h8F, a);
    assign q[8]  = lut_bit(8'hC4, a);
    assign q[7]  = lut_bit(8'h26, a);
    assign q[6]  = lut_bit(8'h36, a);
    assign q[5]  = lut_bit(8'h53, a);
    assign q[4]  = lut_bit(8'h85, a);
    assign q[3]  = lut_bit(8'hA8, a);
    assign q[2]  = lut_bit(8'h7C, a);
    assign q[1]  = lut_bit(8'h79, a);
    assign q[0]  = lut_bit(8'h80, a);
endmodule