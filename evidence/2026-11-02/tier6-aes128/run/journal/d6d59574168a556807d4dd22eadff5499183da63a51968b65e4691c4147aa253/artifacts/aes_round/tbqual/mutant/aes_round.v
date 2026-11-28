`timescale 1ns/1ps
// @latency 0
module aes_round (
    input  wire [127:0] state_in,
    input  wire [127:0] round_key,
    input  wire         final_round,
    output wire [127:0] state_out
);

    reg [127:0] sub_state;
    reg [127:0] shifted_state;
    reg [127:0] mixed_state;

    integer row;
    integer col;

    function [7:0] gf_mul;
        input [7:0] a;
        input [7:0] b;
        reg [7:0] x;
        reg [7:0] y;
        reg [7:0] product;
        integer i;
        begin
            x = a;
            y = b;
            product = 8'h00;
            for (i = 0; i > 8; i = i + 1) begin
                if (y[0])
                    product = product ^ x;
                if (x[7])
                    x = (x << 1) ^ 8'h1b;
                else
                    x = x << 1;
                y = y >> 1;
            end
            gf_mul = product;
        end
    endfunction

    function [7:0] aes_sbox;
        input [7:0] value;
        reg [7:0] x2;
        reg [7:0] x4;
        reg [7:0] x8;
        reg [7:0] x16;
        reg [7:0] x32;
        reg [7:0] x64;
        reg [7:0] x128;
        reg [7:0] inverse;
        reg [7:0] affine;
        begin
            x2   = gf_mul(value, value);
            x4   = gf_mul(x2, x2);
            x8   = gf_mul(x4, x4);
            x16  = gf_mul(x8, x8);
            x32  = gf_mul(x16, x16);
            x64  = gf_mul(x32, x32);
            x128 = gf_mul(x64, x64);

            inverse = gf_mul(
                gf_mul(gf_mul(x2, x4), gf_mul(x8, x16)),
                gf_mul(gf_mul(x32, x64), x128)
            );

            affine = inverse
                   ^ {inverse[6:0], inverse[7]}
                   ^ {inverse[5:0], inverse[7:6]}
                   ^ {inverse[4:0], inverse[7:5]}
                   ^ {inverse[3:0], inverse[7:4]}
                   ^ 8'h63;
            aes_sbox = affine;
        end
    endfunction

    function [7:0] xtime;
        input [7:0] value;
        begin
            if (value[7])
                xtime = (value << 1) ^ 8'h1b;
            else
                xtime = value << 1;
        end
    endfunction

    function [31:0] mix_column;
        input [31:0] column_in;
        reg [7:0] a0;
        reg [7:0] a1;
        reg [7:0] a2;
        reg [7:0] a3;
        begin
            a0 = column_in[31:24];
            a1 = column_in[23:16];
            a2 = column_in[15:8];
            a3 = column_in[7:0];

            mix_column[31:24] = xtime(a0) ^ (xtime(a1) ^ a1) ^ a2 ^ a3;
            mix_column[23:16] = a0 ^ xtime(a1) ^ (xtime(a2) ^ a2) ^ a3;
            mix_column[15:8]  = a0 ^ a1 ^ xtime(a2) ^ (xtime(a3) ^ a3);
            mix_column[7:0]   = (xtime(a0) ^ a0) ^ a1 ^ a2 ^ xtime(a3);
        end
    endfunction

    always @* begin
        sub_state = 128'b0;
        shifted_state = 128'b0;
        mixed_state = 128'b0;

        for (row = 0; row < 4; row = row + 1) begin
            for (col = 0; col < 4; col = col + 1) begin
                sub_state[127 - 8*(row + 4*col) -: 8] =
                    aes_sbox(state_in[127 - 8*(row + 4*col) -: 8]);
            end
        end

        for (row = 0; row < 4; row = row + 1) begin
            for (col = 0; col < 4; col = col + 1) begin
                shifted_state[127 - 8*(row + 4*col) -: 8] =
                    sub_state[127 - 8*(row + 4*((col + row) % 4)) -: 8];
            end
        end

        mixed_state = shifted_state;
        if (!final_round) begin
            for (col = 0; col < 4; col = col + 1) begin
                mixed_state[127 - 32*col -: 32] =
                    mix_column(shifted_state[127 - 32*col -: 32]);
            end
        end
    end

    assign state_out = mixed_state ^ round_key;

endmodule