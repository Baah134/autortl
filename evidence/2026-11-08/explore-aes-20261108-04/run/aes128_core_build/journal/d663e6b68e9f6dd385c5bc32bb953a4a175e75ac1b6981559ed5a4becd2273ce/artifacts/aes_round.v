`timescale 1ns/1ps
// @latency 0
module aes_round (
    input  wire [127:0] state_in,
    input  wire [127:0] round_key,
    input  wire         final_round,
    output wire [127:0] state_out
);

    function [7:0] gf_multiply;
        input [7:0] left;
        input [7:0] right;
        reg [7:0] a;
        reg [7:0] b;
        reg [7:0] result;
        integer j;
        begin
            a = left;
            b = right;
            result = 8'h00;
            for (j = 0; j < 8; j = j + 1) begin
                if (b[0])
                    result = result ^ a;
                if (a[7])
                    a = {a[6:0], 1'b0} ^ 8'h1b;
                else
                    a = {a[6:0], 1'b0};
                b = {1'b0, b[7:1]};
            end
            gf_multiply = result;
        end
    endfunction

    function [7:0] aes_sbox;
        input [7:0] value;
        reg [7:0] inverse;
        reg [7:0] base;
        integer i;
        begin
            inverse = 8'h01;
            base = value;
            for (i = 7; i >= 0; i = i - 1) begin
                if ((8'hfe >> i) & 1)
                    inverse = gf_multiply(inverse, base);
                base = gf_multiply(base, base);
            end
            if (value == 8'h00)
                inverse = 8'h00;
            aes_sbox = inverse
                     ^ {inverse[6:0], inverse[7]}
                     ^ {inverse[5:0], inverse[7:6]}
                     ^ {inverse[4:0], inverse[7:5]}
                     ^ {inverse[3:0], inverse[7:4]}
                     ^ 8'h63;
        end
    endfunction

    function [7:0] xtime;
        input [7:0] value;
        begin
            xtime = {value[6:0], 1'b0} ^ (value[7] ? 8'h1b : 8'h00);
        end
    endfunction

    wire [127:0] substituted;
    wire [127:0] shifted;
    wire [127:0] mixed;

    genvar n;
    generate
        for (n = 0; n < 16; n = n + 1) begin : gen_sub
            assign substituted[127 - 8*n -: 8] =
                aes_sbox(state_in[127 - 8*n -: 8]);
        end
    endgenerate

    genvar row;
    genvar col;
    generate
        for (col = 0; col < 4; col = col + 1) begin : gen_shift_col
            for (row = 0; row < 4; row = row + 1) begin : gen_shift_row
                localparam integer SOURCE_COL = (col + row) % 4;
                assign shifted[127 - 8*(4*col + row) -: 8] =
                    substituted[127 - 8*(4*SOURCE_COL + row) -: 8];
            end
        end
    endgenerate

    genvar c;
    generate
        for (c = 0; c < 4; c = c + 1) begin : gen_mix
            wire [7:0] a0, a1, a2, a3;
            assign a0 = shifted[127 - 8*(4*c + 0) -: 8];
            assign a1 = shifted[127 - 8*(4*c + 1) -: 8];
            assign a2 = shifted[127 - 8*(4*c + 2) -: 8];
            assign a3 = shifted[127 - 8*(4*c + 3) -: 8];

            assign mixed[127 - 8*(4*c + 0) -: 8] =
                xtime(a0) ^ (xtime(a1) ^ a1) ^ a2 ^ a3;
            assign mixed[127 - 8*(4*c + 1) -: 8] =
                a0 ^ xtime(a1) ^ (xtime(a2) ^ a2) ^ a3;
            assign mixed[127 - 8*(4*c + 2) -: 8] =
                a0 ^ a1 ^ xtime(a2) ^ (xtime(a3) ^ a3);
            assign mixed[127 - 8*(4*c + 3) -: 8] =
                (xtime(a0) ^ a0) ^ a1 ^ a2 ^ xtime(a3);
        end
    endgenerate

    assign state_out = (final_round ? shifted : mixed) ^ round_key;

endmodule