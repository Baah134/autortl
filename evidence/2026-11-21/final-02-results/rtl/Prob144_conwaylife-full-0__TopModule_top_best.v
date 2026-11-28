`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output wire [255:0] q
);

    reg [255:0] state;
    wire [255:0] next_state;
    (* keep = "true" *) wire [255:0] vertical_parity;
    (* keep = "true" *) wire [255:0] vertical_majority;

    assign q = state;

    function [31:0] partial_sum_table;
        input integer code_bit;
        integer index;
        integer total;
        reg [1:0] code;
        begin
            for (index = 0; index < 32; index = index + 1) begin
                total = {30'b0, index[4:3]} + {30'b0, index[2:1]}
                      + {31'b0, index[0]};
                // Only partial totals of 1 through 3 can reach 2 or 3.
                code = ((total >= 1) && (total <= 3)) ? total[1:0] : 2'b00;
                partial_sum_table[index] = code[code_bit];
            end
        end
    endfunction

    localparam [31:0] PARTIAL_LOW  = partial_sum_table(0);
    localparam [31:0] PARTIAL_HIGH = partial_sum_table(1);

    genvar row, col;
    generate
        for (row = 0; row < 16; row = row + 1) begin : gen_row
            for (col = 0; col < 16; col = col + 1) begin : gen_col
                localparam integer CENTER = 16 * row + col;
                localparam integer ABOVE  = 16 * ((row + 15) % 16) + col;
                localparam integer BELOW  = 16 * ((row + 1) % 16) + col;
                localparam integer LEFT   = 16 * row + ((col + 15) % 16);
                localparam integer RIGHT  = 16 * row + ((col + 1) % 16);

                wire [4:0] partial_index;
                (* keep = "true" *) wire [1:0] partial_code;
                wire evolved;

                assign vertical_parity[CENTER] =
                    state[ABOVE] ^ state[CENTER] ^ state[BELOW];
                assign vertical_majority[CENTER] =
                    (state[ABOVE] & state[CENTER]) |
                    (state[ABOVE] & state[BELOW]) |
                    (state[CENTER] & state[BELOW]);

                assign partial_index = {
                    vertical_majority[LEFT], vertical_parity[LEFT],
                    vertical_majority[RIGHT], vertical_parity[RIGHT],
                    state[ABOVE]
                };
                assign partial_code[0] = PARTIAL_LOW[partial_index];
                assign partial_code[1] = PARTIAL_HIGH[partial_index];

                assign evolved = state[BELOW] ?
                    ((partial_code == 2'd2) |
                     ((partial_code == 2'd1) & state[CENTER])) :
                    ((partial_code == 2'd3) |
                     ((partial_code == 2'd2) & state[CENTER]));

                // A load can define every bit even when the prior board is unknown.
                assign next_state[CENTER] = load ? data[CENTER] : evolved;
            end
        end
    endgenerate

    always @(posedge clk) begin
        state <= next_state;
    end

endmodule